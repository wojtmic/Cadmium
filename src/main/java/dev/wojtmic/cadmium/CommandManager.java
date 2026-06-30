package dev.wojtmic.cadmium;

import org.bukkit.Bukkit;
import org.bukkit.command.Command;
import org.bukkit.command.CommandMap;
import org.bukkit.command.CommandSender;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.logging.Logger;

public class CommandManager {

    private final CommandMap commandMap;
    private final Map<String, CadmiumCommand> registered = new HashMap<>();
    private final Logger logger;

    // Non-null while a reload is in progress.
    // Contains the names of commands that existed before the reload and haven't
    // been re-registered yet; any still present after finishReload() get removed.
    private Set<String> reloadPending = null;
    private boolean structuralChange = false;

    public CommandManager(Logger logger) {
        this.logger = logger;
        this.commandMap = Bukkit.getCommandMap();
    }

    public interface Executor {
        void execute(CommandSender sender, String label, String[] args);
    }

    public interface Completer {
        List<String> complete(CommandSender sender, String label, String[] args);
    }

    /**
     * Begin a reload cycle. Existing commands are kept alive in the brigadier
     * tree but their executors are nulled so any in-flight call during reload
     * gets a safe "reloading" response instead of hitting the closed context.
     */
    public void startReload() {
        reloadPending = new HashSet<>(registered.keySet());
        structuralChange = false;
        for (CadmiumCommand cmd : registered.values()) {
            cmd.executor = null;
            cmd.completer = null;
        }
    }

    public void register(String name, org.graalvm.polyglot.Value pyExecutor, org.graalvm.polyglot.Value pyCompleter) {
        if (commandMap == null) {
            logger.severe("Cannot register command '" + name + "': command map unavailable.");
            return;
        }

        String key = name.toLowerCase();
        Executor executor = pyExecutor.as(Executor.class);
        Completer completer = (pyCompleter != null && !pyCompleter.isNull())
                ? pyCompleter.as(Completer.class)
                : null;

        if (reloadPending != null) {
            reloadPending.remove(key);
            CadmiumCommand existing = registered.get(key);
            if (existing != null) {
                // Update in place — the brigadier node already points here, no re-registration needed.
                existing.executor = executor;
                existing.completer = completer;
                return;
            }
            structuralChange = true;
        }

        // First-time registration (or new command added during reload).
        CadmiumCommand cmd = new CadmiumCommand(name, executor, completer);
        commandMap.register("cadmium", cmd);
        registered.put(key, cmd);
    }

    /**
     * End a reload cycle. Removes commands that were not re-registered by
     * the new script, and returns true if the brigadier tree needs a sync
     * (i.e. commands were added or removed, not merely updated).
     */
    public boolean finishReload() {
        if (reloadPending == null) return false;
        for (String name : reloadPending) {
            CadmiumCommand existing = registered.remove(name);
            if (existing != null) {
                existing.unregister(commandMap);
                structuralChange = true;
            }
        }
        reloadPending = null;
        boolean changed = structuralChange;
        structuralChange = false;
        return changed;
    }

    public void unregister(String name) {
        CadmiumCommand existing = registered.remove(name.toLowerCase());
        if (existing == null) return;
        existing.unregister(commandMap);
    }

    public void unregisterAll() {
        for (String name : List.copyOf(registered.keySet())) {
            unregister(name);
        }
    }

    private static class CadmiumCommand extends Command {
        volatile Executor executor;
        volatile Completer completer;

        protected CadmiumCommand(String name, Executor executor, Completer completer) {
            super(name);
            this.executor = executor;
            this.completer = completer;
        }

        @Override
        public boolean execute(CommandSender sender, String label, String[] args) {
            Executor e = this.executor;
            if (e == null) {
                sender.sendMessage("This command is currently reloading, please try again.");
                return true;
            }
            e.execute(sender, label, args);
            return true;
        }

        @Override
        public List<String> tabComplete(CommandSender sender, String alias, String[] args) {
            Completer c = this.completer;
            if (c == null) return List.of();
            List<String> result = c.complete(sender, alias, args);
            return result == null ? List.of() : result;
        }
    }
}
