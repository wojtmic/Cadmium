package dev.wojtmic.cadmium;

import io.papermc.paper.command.brigadier.Commands;
import io.papermc.paper.plugin.lifecycle.event.types.LifecycleEvents;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.minimessage.MiniMessage;
import org.bukkit.event.HandlerList;
import org.bukkit.plugin.java.JavaPlugin;
import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.PolyglotException;
import org.graalvm.polyglot.Source;
import org.graalvm.python.embedding.GraalPyResources;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import com.moandjiezana.toml.Toml;

public final class Cadmium extends JavaPlugin {

    private Context context;
    private Bridge bridge;
    private CommandManager commandManager;
    private CoroutineScheduler coroutineScheduler;

    public static File dataFolder;
    public static File pluginFile;
    public static String namespacePrefix = "cadmium";
    public static String uvOverride = "auto";
    public static boolean autoSync = true;

    public void reload(boolean failFast, String entrypoint) {
        if (bridge != null) {
            HandlerList.unregisterAll(bridge);
            bridge = null;
        }
        if (commandManager == null) {
            commandManager = new CommandManager(getLogger());
        } else {
            commandManager.startReload();
        }
        if (context != null) {
            try {
                context.eval("python", "import cadmium.schedule as _every_mod; print('cancelling', len(_every_mod._scheduled_tasks)); _every_mod.cancel_all_tasks()");
            } catch (Exception e) {
                getLogger().warning("Failed to cancel scheduled tasks: " + e);
            }
            if (coroutineScheduler != null) {
                coroutineScheduler.shutdown();
                coroutineScheduler = null;
            }
            context.close();
            context = null;
        }

        UvManager uv = new UvManager(getLogger());
        try {
            uv.setup();
        } catch (IOException | InterruptedException e) {
            getComponentLogger().error("An exception occurred while setting up uv:");
            getComponentLogger().error(e.toString());
            return;
        }

        context = GraalPyResources.contextBuilder(getDataFolder().toPath().toAbsolutePath())
                .allowAllAccess(true)
//                .option("python.PosixModuleBackend", "native")
                .hostClassLoader(getClassLoader())
                .allowHostClassLookup(className -> true)
                .build();

        try {
            Path dataFolder = getDataFolder().toPath().toAbsolutePath();
            context.eval("python", "import sys; sys.path.insert(0, '" + dataFolder + "')");
            context.eval("python", "import sys; sys.path.insert(0, '" + uv.getBundledPython() + "')");

            context.getBindings("python").putMember("_command_manager", commandManager);
            context.getBindings("python").putMember("_plugin", this);
            context.getBindings("python").putMember("_cadmium_namespace", namespacePrefix);
            context.eval("python", "import builtins; builtins._command_manager = _command_manager; builtins._plugin = _plugin; builtins._cadmium_namespace = _cadmium_namespace");

            coroutineScheduler = new CoroutineScheduler(this, context, getLogger());
            context.getBindings("python").putMember("_coroutine_manager", coroutineScheduler);
            context.eval("python", "import builtins; builtins._coroutine_manager = _coroutine_manager");

            Path script = getDataFolder().toPath().resolve(entrypoint);
            context.eval(Source.newBuilder("python", script.toFile()).build());

            bridge = new Bridge(context);
            getServer().getPluginManager().registerEvents(bridge, this);

            boolean needsSync = commandManager.finishReload();
            if (needsSync) {
                try {
                    getServer().getClass().getMethod("syncCommands").invoke(getServer());
                } catch (ReflectiveOperationException ex) {
                    getLogger().warning("Could not sync commands: " + ex.getMessage());
                }
            }
        } catch (IOException | PolyglotException e) {
//        } catch (IOException e) { // uncomment this and comment above when testing to see full errors, leave this commented and the thing above uncommented in builds
            commandManager.finishReload();
            getComponentLogger().error("An exception occurred while loading Python:");
            getComponentLogger().error(e.getMessage());
            if (failFast) {
                getComponentLogger().error("Because of Cadmium config, shutting down server due to script loading failure!");
                getServer().shutdown();
            }
        }
    }

    @Override
    public void onEnable() {
        dataFolder = getDataFolder();
        pluginFile = getFile();
        dataFolder.mkdirs();
        Path dataPath = dataFolder.toPath();
        try {
            Path mainPy = dataPath.resolve("main.py");
            if (!Files.exists(mainPy)) Files.createFile(mainPy);

            Path pyproject = dataPath.resolve("pyproject.toml");
            if (!Files.exists(pyproject)) {
                Files.createFile(pyproject);
                String content = """
                        [project]
                        name = "cadmium-server-scripts"
                        version = "0.1.0"
                        description = "CHANGEME"
                        
                        requires-python = "==3.12.*" # DO NOT CHANGE THIS! Cadmium will ONLY work with Python 3.12
                        dependencies = [] # Recommended to add dependencies with `uv add`
                        
                        [tool.uv]
                        managed = true
                        
                        # main Cadmium configuration
                        # requires a server restart to reload
                        [tool.cadmium]
                        # will abort server start if main file loading fails with an error
                        # recommended to turn on in public production
                        # default: false
                        abort-start-on-fail = false
                        # will shut down server if reload fails
                        # default: false
                        shutdown-on-reload-fail = false
                        # if disabled the /cadmium (/cad) command will not be registered
                        # default: true
                        enable-cad-command = true
                        # controls which .py file to load as main
                        # default: main.py
                        main-code = "main.py"
                        # if disabled will not sync (manage dependencies) automatically
                        # default: true
                        auto-sync = true
                        # path to the uv binary Cadmium will use to manage dependencies
                        # set to "auto" to use a system-wide uv install, downloading a binary if none is found
                        # set to "system" to always use a system-wide uv install (Cadmium will not load if not found)
                        # set to "download" to always use a Cadmium-downloaded binary
                        # set to an explicit path to force that binary (Cadmium will not load if it's not found)
                        # default: auto
                        uv-path = "auto"
                        # namespace used for script-registered commands, attributes, etc.
                        # (e.g. /<prefix>:<command>)
                        # default: cadmium
                        namespace-prefix = "cadmium"
                        """;

                try {
                    Files.writeString(pyproject, content);
                } catch (IOException e) {
                    getComponentLogger().error("Unable to write default configuration!");
                }
            }


        } catch (IOException e) {
            getComponentLogger().error("Failed to create default files: " + e.getMessage());
            return;
        }

        Path pyproject = dataPath.resolve("pyproject.toml");
        Toml toml = new Toml().read(pyproject.toFile());

        boolean failFast = toml.getBoolean("tool.cadmium.abort-start-on-fail", false);
        boolean failReload = toml.getBoolean("tool.cadmium.shutdown-on-reload-fail", false);
        boolean cadCommand = toml.getBoolean("tool.cadmium.enable-cad-command", true);
        boolean autoSync = toml.getBoolean("tool.cadmium.auto-sync", true);
        String entrypoint = toml.getString("tool.cadmium.main-code", "main.py");
        String uvOverride = toml.getString("tool.cadmium.uv-path", "auto");
        String namespacePrefix = toml.getString("tool.cadmium.namespace-prefix", "cadmium");

        Cadmium.namespacePrefix = namespacePrefix;
        Cadmium.autoSync = autoSync;
        Cadmium.uvOverride = uvOverride;

        reload(failFast, entrypoint);

        if (cadCommand) {
            getLifecycleManager().registerEventHandler(LifecycleEvents.COMMANDS, event -> {
                var reloadNode = Commands.literal("reload")
                        .executes(ctx -> {
                            reload(failReload, entrypoint);
                            Component msg = MiniMessage.miniMessage().deserialize("<green>Reloaded!");
                            ctx.getSource().getSender().sendMessage(msg);
                            return 1;
                        });

                java.util.function.Predicate<io.papermc.paper.command.brigadier.CommandSourceStack> hasPerm =
                        source -> source.getSender().hasPermission("cadmium.admin");

                event.registrar().register(
                        Commands.literal("cadmium")
                                .requires(hasPerm)
                                .then(reloadNode)
                                .build()
                );

                event.registrar().register(
                        Commands.literal("cad")
                                .requires(hasPerm)
                                .then(reloadNode)
                                .build()
                );
            });
        }

    }

    @Override
    public void onDisable() {
        if (bridge != null) HandlerList.unregisterAll(bridge);
        if (coroutineScheduler != null) coroutineScheduler.shutdown();
        if (context != null) context.close();
    }
}