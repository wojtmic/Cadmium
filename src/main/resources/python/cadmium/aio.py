import inspect
from cadmium._async import _Resume, _start_async_task, _poll_async_task


def _resolve_anchor(near):
    if near is None:
        return None
    return getattr(near, "raw", near)


class _Awaitable:
    def __await__(self):
        result = yield self
        return result


class WaitTicks(_Awaitable):
    def __init__(self, ticks: int, near=None):
        if ticks < 0:
            raise ValueError("ticks must be >= 0")
        self.ticks = ticks
        self.anchor = _resolve_anchor(near)

    def _to_resume(self, token):
        return _Resume("ticks", token, ticks=self.ticks, anchor=self.anchor)


class NextEvent(_Awaitable):
    def __init__(self, event, near=None, filter=None, timeout_ticks: int | None = None):
        self.event = event
        self.anchor = _resolve_anchor(near)
        self.filter = filter
        self.timeout_ticks = timeout_ticks

    def _to_resume(self, token):
        return _Resume(
            "event", token,
            event_name=self.event.value,
            filter=self.filter,
            anchor=self.anchor,
            timeout_ticks=self.timeout_ticks,
        )


class RunAsync:
    def __init__(self, coro, near=None):
        if not inspect.iscoroutine(coro):
            raise TypeError("run_async expects an asyncio coroutine, e.g. client.get(url)")
        self._coro = coro
        self._anchor = _resolve_anchor(near)

    def __await__(self):
        task = _start_async_task(self._coro)
        while True:
            done, value = _poll_async_task(task)
            if done:
                if isinstance(value, BaseException):
                    raise value
                return value
            yield _TickResume(self._anchor)


class _TickResume:
    __slots__ = ("anchor",)

    def __init__(self, anchor):
        self.anchor = anchor

    def _to_resume(self, token):
        return _Resume("ticks", token, ticks=1, anchor=self.anchor)


def wait_ticks(ticks: int, near=None) -> WaitTicks:
    return WaitTicks(ticks, near=near)


def next_event(event, near=None, filter=None, timeout_ticks: int | None = None) -> NextEvent:
    return NextEvent(event, near=near, filter=filter, timeout_ticks=timeout_ticks)


def run_async(coro, near=None) -> RunAsync:
    return RunAsync(coro, near=near)