import functools
from typing import Any, Callable, ParamSpec, TypeVar

from app.core.config import config


Params = ParamSpec('Params')
Return = TypeVar('Return')


def testing_override(
        testing_function: Callable[..., Any],
        /,
    ) -> Callable[[Callable[Params, Return]], Callable[Params, Return]]:
    """
    Decorator factory that replaces the decorated function with the
    given testing function if the global testing mode is enabled in
    the app config, and returns the original function otherwise.

    >>> def fake_addition(a: int, b: int) -> int:
    ...     return 999
    >>> @testing_override(fake_addition)
    ... def addition(a: int, b: int) -> int:
    ...     return a + b

    Args:
        testing_function: Function to use when testing mode is enabled.

    Returns:
        Decorator that replaces the decorated function with the given
        testing function if the global testing mode is enabled in the
        app config, and returns the original function otherwise.
    """

    def decorator(func: Callable[Params, Return]) -> Callable[Params, Return]:
        if config.TESTING_MODE:
            @functools.wraps(func)
            def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
                return testing_function(*args, **kwargs)
            return wrapper
        return func

    return decorator
