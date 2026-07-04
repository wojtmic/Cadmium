import java

_BukkitRunnable = java.type("org.bukkit.scheduler.BukkitRunnable")

_scheduled_tasks = []


def every(ticks: int, delay: int = 0):
    def decorator(func):
        class _Task(_BukkitRunnable):
            def run(self):
                func()

        task = _Task()
        _scheduled_tasks.append(task)
        task.runTaskTimer(_plugin, delay, ticks)
        return func
    return decorator


def cancel_all_tasks():
    for task in _scheduled_tasks:
        try:
            task.cancel()
        except Exception:
            pass
    _scheduled_tasks.clear()