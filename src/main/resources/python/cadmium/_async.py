import asyncio
import inspect

_coroutines: dict[int, object] = {}
_not_yet_started: set[int] = set()
_first_step_args: dict[int, tuple] = {}
_next_token = 0

_loop = asyncio.new_event_loop()


class _Resume:
    __slots__ = (
        "kind", "token", "message", "ticks", "anchor",
        "timeout_ticks", "event_name", "filter", "result", "fn",
    )

    def __init__(self, kind, token, **kwargs):
        self.kind = kind
        self.token = token
        self.message = kwargs.get("message")
        self.ticks = kwargs.get("ticks")
        self.anchor = kwargs.get("anchor")
        self.timeout_ticks = kwargs.get("timeout_ticks")
        self.event_name = kwargs.get("event_name")
        self.filter = kwargs.get("filter")
        self.result = kwargs.get("result")
        self.fn = kwargs.get("fn")


def is_async_callable(func) -> bool:
    return inspect.iscoroutinefunction(func)


def _async_start(coro_func, *args) -> int:
    global _next_token
    coro = coro_func(*args)
    token = _next_token
    _next_token += 1
    _coroutines[token] = coro
    _not_yet_started.add(token)
    _first_step_args[token] = args
    return token


def _close_cancel_windows(args):
    for arg in args:
        closer = getattr(arg, "_close_cancel_window", None)
        if closer is not None:
            closer()


def _start_async_task(coro) -> "asyncio.Task":
    return _loop.create_task(coro)


def _poll_async_task(task) -> tuple[bool, object]:
    _loop.run_until_complete(asyncio.sleep(0))

    if not task.done():
        return (False, None)

    try:
        return (True, task.result())
    except BaseException as e:
        return (True, e)


_ERROR_TYPES = {
    "TimeoutError": TimeoutError,
    "RuntimeError": RuntimeError,
}


def _async_step(token: int, send_value=None, error=None, error_type="RuntimeError") -> _Resume:
    coro = _coroutines.get(token)
    if coro is None:
        return _Resume("done", token)

    first_step = token in _not_yet_started
    if first_step:
        _not_yet_started.discard(token)
        send_value = None

    try:
        if error is not None and not first_step:
            exc_cls = _ERROR_TYPES.get(error_type, RuntimeError)
            yielded = coro.throw(exc_cls(str(error)))
        else:
            yielded = coro.send(send_value)
    except StopIteration:
        _coroutines.pop(token, None)
        _not_yet_started.discard(token)
        if first_step:
            _close_cancel_windows(_first_step_args.pop(token, ()))
        return _Resume("done", token)
    except BaseException as e:
        _coroutines.pop(token, None)
        _not_yet_started.discard(token)
        if first_step:
            _close_cancel_windows(_first_step_args.pop(token, ()))
        return _Resume("error", token, message=f"{type(e).__name__}: {e}")

    if first_step:
        _close_cancel_windows(_first_step_args.pop(token, ()))

    return yielded._to_resume(token)