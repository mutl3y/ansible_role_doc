import warnings
import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(message: str, version: str) -> Callable[[F], F]:
    """
    Decorator to mark functions as deprecated.

    Issues a DeprecationWarning when the decorated function is called.

    Args:
        message: Deprecation message explaining what to use instead.
        version: Version when the function will be removed.

    Returns:
        Decorated function that issues warning on call.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{message} (deprecated in version {version})",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
