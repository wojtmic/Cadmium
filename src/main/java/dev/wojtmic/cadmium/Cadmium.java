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

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.jar.JarFile;

public final class Cadmium extends JavaPlugin {

    private Context context;
    private Bridge bridge;
    private CommandManager commandManager;

    public void reload() {
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
            context.close();
            context = null;
        }

        UvManager uv = new UvManager(getDataFolder(), getLogger());
        try {
            uv.setup();
        } catch (IOException | InterruptedException e) {
            getComponentLogger().error("An exception occurred while setting up uv:");
            getComponentLogger().error(e.toString());
            return;
        }

        Path bundledPython;
        try {
            bundledPython = extractBundledPython();
        } catch (IOException e) {
            getComponentLogger().error("Failed to extract bundled Python module:");
            getComponentLogger().error(e.toString());
            return;
        }

        context = Context.newBuilder("python")
                .allowAllAccess(true)
                .option("python.PosixModuleBackend", "native")
                .hostClassLoader(getClassLoader())
                .allowHostClassLookup(className -> true)
                .build();

        try {
            Path sitePackages = uv.getSitePackages();
            Path dataFolder = getDataFolder().toPath().toAbsolutePath();
            context.eval("python", "import sys; sys.path.insert(0, '" + dataFolder + "')");
            context.eval("python", "import sys; sys.path.insert(0, '" + sitePackages + "')");
            context.eval("python", "import sys; sys.path.insert(0, '" + bundledPython + "')");

            context.getBindings("python").putMember("_command_manager", commandManager);
            context.eval("python", "import builtins; builtins._command_manager = _command_manager");

            Path script = getDataFolder().toPath().resolve("main.py");
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
        }
    }

    private Path extractBundledPython() throws IOException {
        Path dest = getDataFolder().toPath().resolve(".cadmium_bundle");
        Files.createDirectories(dest);
        try (JarFile jar = new JarFile(getFile())) {
            jar.stream()
                .filter(e -> e.getName().startsWith("python/") && !e.isDirectory())
                .forEach(e -> {
                    try {
                        String relative = e.getName().substring("python/".length());
                        Path target = dest.resolve(relative);
                        Files.createDirectories(target.getParent());
                        try (InputStream is = jar.getInputStream(e)) {
                            Files.copy(is, target, StandardCopyOption.REPLACE_EXISTING);
                        }
                    } catch (IOException ex) {
                        throw new UncheckedIOException(ex);
                    }
                });
        } catch (UncheckedIOException e) {
            throw e.getCause();
        }
        return dest;
    }

    @Override
    public void onEnable() {
        getDataFolder().mkdirs();
        Path dataPath = getDataFolder().toPath();
        try {
            Path mainPy = dataPath.resolve("main.py");
            if (!Files.exists(mainPy)) Files.createFile(mainPy);
            Path requirementsTxt = dataPath.resolve("requirements.txt");
            if (!Files.exists(requirementsTxt)) Files.createFile(requirementsTxt);
        } catch (IOException e) {
            getComponentLogger().error("Failed to create default files: " + e.getMessage());
            return;
        }

        reload();
        getLifecycleManager().registerEventHandler(LifecycleEvents.COMMANDS, event -> {
            event.registrar().register(
                    Commands.literal("cad")
                            .then(Commands.literal("reload")
                                    .executes(ctx -> {
                                        reload();
                                        Component msg = MiniMessage.miniMessage().deserialize("<green>Reloaded!");
                                        ctx.getSource().getSender().sendMessage(msg);
                                        return 1;
                                    }))
                            .build()
            );
        });
    }

    @Override
    public void onDisable() {
        if (bridge != null) HandlerList.unregisterAll(bridge);
        if (context != null) context.close();
    }
}