package dev.wojtmic.cadmium;

import org.bukkit.Bukkit;
import org.bukkit.plugin.Plugin;
import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.Value;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Logger;

public class CoroutineScheduler {

    private final Plugin plugin;
    private final Context context;
    private final Logger logger;

    private final Value asyncStart;
    private final Value asyncStep;

    private final Map<String, List<EventWaiter>> eventWaiters = new ConcurrentHashMap<>();

    public CoroutineScheduler(Plugin plugin, Context context, Logger logger) {
        this.plugin = plugin;
        this.context = context;
        this.logger = logger;

        Value cadmiumAsync = context.eval("python", "import cadmium._async; cadmium._async");
        this.asyncStart = cadmiumAsync.getMember("_async_start");
        this.asyncStep = cadmiumAsync.getMember("_async_step");
    }

    public void start(Value coroFunc, Object arg, Object near) {
        Value token = asyncStart.execute(coroFunc, arg);
        runAnchored(near, () -> step(token, null, null));
    }

    public void start(Value coroFunc, Object arg) {
        start(coroFunc, arg, null);
    }

    private void step(Value token, Object sendValue, Object error) {
        Value resume;
        try {
            resume = asyncStep.execute(token, sendValue, error);
        } catch (RuntimeException e) {
            logger.severe("Internal error stepping async coroutine: " + e);
            return;
        }

        String kind = resume.getMember("kind").asString();
        switch (kind) {
            case "done" -> {
            }
            case "error" -> {
                String message = resume.getMember("message").asString();
                logger.warning("Unhandled exception in async handler: " + message);
            }
            case "ticks" -> {
                long ticks = resume.getMember("ticks").asLong();
                Object anchor = unwrapAnchor(resume.getMember("anchor"));
                scheduleDelayed(anchor, ticks, () -> step(token, null, null));
            }
            case "event" -> registerEventWaiter(token, resume);
            default -> logger.severe("Unknown async resume kind: " + kind);
        }
    }

    private void registerEventWaiter(Value token, Value resume) {
        String eventName = resume.getMember("event_name").asString();
        Value filter = resume.getMember("filter");
        boolean hasFilter = filter != null && !filter.isNull();
        Object anchor = unwrapAnchor(resume.getMember("anchor"));
        Value timeoutTicksValue = resume.getMember("timeout_ticks");
        Long timeoutTicks = (timeoutTicksValue != null && !timeoutTicksValue.isNull())
                ? timeoutTicksValue.asLong() : null;

        EventWaiter waiter = new EventWaiter(token, hasFilter ? filter : null, anchor);
        eventWaiters.computeIfAbsent(eventName, k -> new CopyOnWriteArrayList<>()).add(waiter);

        if (timeoutTicks != null) {
            String timeoutMessage = "next_event('" + eventName + "') timed out after "
                    + timeoutTicks + " ticks";
            scheduleDelayed(anchor, timeoutTicks, () -> {
                if (waiter.resolved.compareAndSet(false, true)) {
                    removeWaiter(eventName, waiter);
                    step(token, null, timeoutMessage);
                }
            });
        }
    }

    private void removeWaiter(String eventName, EventWaiter waiter) {
        List<EventWaiter> waiters = eventWaiters.get(eventName);
        if (waiters != null) waiters.remove(waiter);
    }

    public void notify_event(String eventName, Object eventObj) {
        List<EventWaiter> waiters = eventWaiters.get(eventName);
        if (waiters == null || waiters.isEmpty()) return;

        for (EventWaiter waiter : List.copyOf(waiters)) {
            if (waiter.resolved.get()) continue;

            if (waiter.filter != null) {
                boolean matches;
                try {
                    matches = waiter.filter.execute(eventObj).asBoolean();
                } catch (RuntimeException e) {
                    logger.warning("Error evaluating next_event filter, dropping waiter: " + e);
                    if (waiter.resolved.compareAndSet(false, true)) {
                        removeWaiter(eventName, waiter);
                    }
                    continue;
                }
                if (!matches) continue;
            }

            if (waiter.resolved.compareAndSet(false, true)) {
                removeWaiter(eventName, waiter);
                scheduleDelayed(waiter.anchor, 0, () -> step(waiter.token, eventObj, null));
            }
        }
    }

    private static final class EventWaiter {
        final Value token;
        final Value filter;
        final Object anchor;
        final AtomicBoolean resolved = new AtomicBoolean(false);

        EventWaiter(Value token, Value filter, Object anchor) {
            this.token = token;
            this.filter = filter;
            this.anchor = anchor;
        }
    }

    private Object unwrapAnchor(Value anchorValue) {
        if (anchorValue == null || anchorValue.isNull()) return null;
        return anchorValue.isHostObject() ? anchorValue.asHostObject() : null;
    }

    private void runAnchored(Object anchor, Runnable task) {
        scheduleDelayed(anchor, 0, task);
    }

    private void scheduleDelayed(Object anchor, long ticks, Runnable task) {
        long delay = Math.max(ticks, 1);

        if (anchor == null) {
            if (ticks <= 0) {
                Bukkit.getGlobalRegionScheduler().run(plugin, scheduledTask -> task.run());
            } else {
                Bukkit.getGlobalRegionScheduler().runDelayed(plugin, scheduledTask -> task.run(), delay);
            }
            return;
        }

        if (anchor instanceof org.bukkit.entity.Entity entity) {
            Runnable onRetired = () -> logger.fine(
                    "Dropping async coroutine: anchor entity was removed before resume");

            var scheduled = (ticks <= 0)
                    ? entity.getScheduler().run(plugin, scheduledTask -> task.run(), onRetired)
                    : entity.getScheduler().runDelayed(plugin, scheduledTask -> task.run(), onRetired, delay);

            if (scheduled == null) {
                onRetired.run();
            }
            return;
        }

        if (anchor instanceof org.bukkit.Location location) {
            if (ticks <= 0) {
                Bukkit.getRegionScheduler().run(plugin, location, scheduledTask -> task.run());
            } else {
                Bukkit.getRegionScheduler().runDelayed(plugin, location, scheduledTask -> task.run(), delay);
            }
            return;
        }

        if (anchor instanceof org.bukkit.block.Block block) {
            scheduleDelayed(block.getLocation(), ticks, task);
            return;
        }

        logger.warning("Unrecognized async anchor type " + anchor.getClass()
                + ", falling back to global scheduler");
        scheduleDelayed(null, ticks, task);
    }

    public void shutdown() {
        eventWaiters.clear();
    }
}