package dev.wojtmic.cadmium;

import io.papermc.paper.command.brigadier.Commands;
import io.papermc.paper.plugin.lifecycle.event.types.LifecycleEvents;
import net.kyori.adventure.audience.Audience;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.minimessage.MiniMessage;
import net.kyori.adventure.text.minimessage.tag.resolver.Placeholder;
import org.bukkit.entity.Player;
import org.bukkit.event.HandlerList;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.plugin.messaging.Messenger;
import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.PolyglotException;
import org.graalvm.polyglot.Source;
import org.graalvm.polyglot.Value;
import org.graalvm.python.embedding.GraalPyResources;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import com.moandjiezana.toml.Toml;

import static dev.wojtmic.cadmium.Utils.getReloadRecipients;

public final class Cadmium extends JavaPlugin {

    private Context context;
    private Bridge bridge;
    private CommandManager commandManager;
    private CoroutineScheduler coroutineScheduler;

    public static File dataFolder;
    public static File pluginFile;
    public static String namespacePrefix = "cadmium";
    public static boolean autoSync = true;

    private void unregisterPluginChannels() {
        Messenger messenger = getServer().getMessenger();
        messenger.unregisterIncomingPluginChannel(this);
        messenger.unregisterOutgoingPluginChannel(this);
    }

    public void reload(boolean failFast, String entrypoint) {
        if (bridge != null) {
            HandlerList.unregisterAll(bridge);
            bridge = null;
        }
        unregisterPluginChannels();
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
        PipManager pip = new PipManager(getLogger());
        try {
            pip.setup();
        } catch (IOException | InterruptedException e) {
            getComponentLogger().error("An exception occurred while setting up pip:");
            getComponentLogger().error(e.toString());
            return;
        }

        ClassLoader combinedLoader = new ClassLoader(getClassLoader()) {
            @Override
            protected Class<?> findClass(String name) throws ClassNotFoundException {
                for (org.bukkit.plugin.Plugin p : getServer().getPluginManager().getPlugins()) {
                    try {
                        return p.getClass().getClassLoader().loadClass(name);
                    } catch (ClassNotFoundException ignored) {}
                }
                throw new ClassNotFoundException(name);
            }
        };

        context = GraalPyResources.contextBuilder(getDataFolder().toPath().toAbsolutePath())
                .allowAllAccess(true)
                .hostClassLoader(combinedLoader)
                .allowHostClassLookup(className -> true)
                .allowNativeAccess(true)
                .build();

        try {
            Path dataFolder = getDataFolder().toPath().toAbsolutePath();
            context.eval("python", "import sys; sys.path.insert(0, '" + dataFolder + "')");
            context.eval("python", "import sys; sys.path.insert(0, '" + pip.getBundledPython() + "')");

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

        } catch (IOException e) {
            commandManager.finishReload();
            throw new RuntimeException("Failed to load Python script: " + e.getMessage(), e);
        } catch (PolyglotException e) {
            commandManager.finishReload();
            Path script = getDataFolder().toPath().resolve(entrypoint);
            context.getBindings("python").putMember("_cadmium_script_path", script.toString());

            Value result = context.eval("python", """
                import traceback
                _cadmium_tb = None
                try:
                    with open(_cadmium_script_path) as _f:
                        exec(compile(_f.read(), _cadmium_script_path, 'exec'), {'__name__': '__main__'})
                except BaseException:
                    _cadmium_tb = traceback.format_exc()
                _cadmium_tb
                """);

            String tb = result.isString() ? result.asString() : null;
            throw new RuntimeException(tb, e);
        }
    }

    @Override
    public void onEnable() {
        long startTime = System.nanoTime();

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
                        dependencies = []
                        
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
                        # namespace used for script-registered commands, attributes, etc.
                        # (e.g. /<prefix>:<command>)
                        # default: cadmium
                        namespace-prefix = "cadmium"

                        # optional: sync your script sources from a git repository on startup
                        # runs once, before pip dependency sync, using a pure-Java git implementation
                        # (no system git binary required)
                        #[tool.cadmium.git]
                        # default: true (only matters if this table is present)
                        #enabled = true
                        #url = "https://github.com/you/your-scripts.git"
                        # branch to clone/checkout; default: repo's default branch
                        #branch = "main"
                        # where to clone into, relative to the plugin data folder
                        # default: "." (the data folder itself)
                        #directory = "."
                        #username = "your-username"
                        # any value starting with "$" is resolved from an environment
                        # variable of that name at load time - use this for secrets
                        # instead of committing them here
                        #password = "$CADMIUM_GIT_PASSWORD"
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
        String namespacePrefix = toml.getString("tool.cadmium.namespace-prefix", "cadmium");

        Cadmium.namespacePrefix = namespacePrefix;
        Cadmium.autoSync = autoSync;

        try {
            new GitManager(getLogger()).setup();
        } catch (IOException e) {
            getComponentLogger().error("Git sync failed: " + e.getMessage());
            if (failFast) {
                getServer().shutdown();
                return;
            }
        }

        try {
            reload(failFast, entrypoint);
        } catch (RuntimeException e) {
            getComponentLogger().error(e.getMessage());
            if (failFast) {
                getServer().shutdown();
            }
        }


        if (cadCommand) {
            getLifecycleManager().registerEventHandler(LifecycleEvents.COMMANDS, event -> {
                var reloadNode = Commands.literal("reload")
                        .executes(ctx -> {
                            Player triggeringPlayer = (ctx.getSource().getSender() instanceof Player p) ? p : null;

                            Component msg1 = MiniMessage.miniMessage().deserialize("[<#FFD93D>Cadmium</#FFD93D>] <gold>Reloading...</gold>");
                            ctx.getSource().getSender().sendMessage(msg1);

                            String senderName = ctx.getSource().getSender().getName();
                            Component msg11 = MiniMessage.miniMessage().deserialize(
                                    "[<#FFD93D>Cadmium</#FFD93D>] <aqua>" + senderName + "</aqua> is reloading"
                            );

                            for (Audience a : getReloadRecipients("cadmium.admin", triggeringPlayer)) {
                                a.sendMessage(msg11);
                            }

                            long start = System.nanoTime();

                            try {
                                reload(failReload, entrypoint);
                            } catch (RuntimeException e) {
                                getComponentLogger().error(e.getMessage());

                                Component msg3 = MiniMessage.miniMessage().deserialize(
                                        "[<#FFD93D>Cadmium</#FFD93D>] <red>Error while reloading!\n<traceback>",
                                        Placeholder.unparsed("traceback", e.getMessage())
                                );
                                ctx.getSource().getSender().sendMessage(msg3);

                                if (failReload) {
                                    getServer().shutdown();
                                }

                                return 0;
                            }

                            long end = System.nanoTime();
                            long elapsed = (end - start ) / 1_000_000;

                            Component msg2 = MiniMessage.miniMessage().deserialize("[<#FFD93D>Cadmium</#FFD93D>] <green>Reloaded in <gold>" + elapsed + "ms</gold>!");
                            ctx.getSource().getSender().sendMessage(msg2);
                            return 1;
                        });
                var dumpstubsNode = Commands.literal("dumpstubs")
                        .executes(ctx -> {
                            String outPath = getDataFolder().toPath().resolve("stub-dump.json").toString();
                            try {
                                dev.wojtmic.cadmium.tools.StubDumper.dump(outPath);
                                Component msg = MiniMessage.miniMessage().deserialize(
                                        "[<#FFD93D>Cadmium</#FFD93D>] <green>Stub dump written to <gold>" + outPath + "</gold>");
                                ctx.getSource().getSender().sendMessage(msg);
                            } catch (java.io.IOException e) {
                                Component msg = MiniMessage.miniMessage().deserialize(
                                        "[<#FFD93D>Cadmium</#FFD93D>] <red>Stub dump failed: <white>" + e.getMessage());
                                ctx.getSource().getSender().sendMessage(msg);
                            }
                            return 1;
                        });
                var pullNode = Commands.literal("pull")
                        .executes(ctx -> {
                            Component msg1 = MiniMessage.miniMessage().deserialize("[<#FFD93D>Cadmium</#FFD93D>] <gold>Pulling...</gold>");
                            ctx.getSource().getSender().sendMessage(msg1);

                            long start = System.nanoTime();

                            try {
                                new GitManager(getLogger()).setup();
                            } catch (java.io.IOException e) {
                                getComponentLogger().error("Git pull failed: " + e.getMessage());
                                Component msg = MiniMessage.miniMessage().deserialize(
                                        "[<#FFD93D>Cadmium</#FFD93D>] <red>Pull failed!\n<traceback>",
                                        Placeholder.unparsed("traceback", e.getMessage()));
                                ctx.getSource().getSender().sendMessage(msg);
                                return 0;
                            }

                            try {
                                reload(failReload, entrypoint);
                            } catch (RuntimeException e) {
                                getComponentLogger().error(e.getMessage());
                                Component msg = MiniMessage.miniMessage().deserialize(
                                        "[<#FFD93D>Cadmium</#FFD93D>] <red>Pulled, but reload failed!\n<traceback>",
                                        Placeholder.unparsed("traceback", e.getMessage()));
                                ctx.getSource().getSender().sendMessage(msg);

                                if (failReload) {
                                    getServer().shutdown();
                                }
                                return 0;
                            }

                            long elapsed = (System.nanoTime() - start) / 1_000_000;
                            Component msg2 = MiniMessage.miniMessage().deserialize(
                                    "[<#FFD93D>Cadmium</#FFD93D>] <green>Pulled and reloaded in <gold>" + elapsed + "ms</gold>!");
                            ctx.getSource().getSender().sendMessage(msg2);
                            return 1;
                        });

                java.util.function.Predicate<io.papermc.paper.command.brigadier.CommandSourceStack> hasPerm =
                        source -> source.getSender().hasPermission("cadmium.admin");

                event.registrar().register(
                        Commands.literal("cadmium")
                                .requires(hasPerm)
                                .then(reloadNode)
                                .then(dumpstubsNode)
                                .then(pullNode)
                                .build()
                );

                event.registrar().register(
                        Commands.literal("cad")
                                .requires(hasPerm)
                                .then(reloadNode)
                                .then(dumpstubsNode)
                                .then(pullNode)
                                .build()
                );
            });
        }

        long elapsed = (System.nanoTime() - startTime) / 1_000_000;
        getComponentLogger().info("Cadmium startup complete in " + elapsed + "ms!");
    }

    @Override
    public void onDisable() {
        if (bridge != null) HandlerList.unregisterAll(bridge);
        unregisterPluginChannels();
        if (coroutineScheduler != null) coroutineScheduler.shutdown();
        if (context != null) context.close();
    }
}