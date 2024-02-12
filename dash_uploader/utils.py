import logging
from packaging import version
import time
import functools

from typing import TypeVar, cast

try:
    from typing import Callable
except ImportError:
    from collections.abc import Callable


_Callable = TypeVar("_Callable", bound=Callable)
T = TypeVar("T")


# Dash version
try:
    import importlib.metadata

    dash_version_str = importlib.metadata.version("dash")
except (ImportError, ModuleNotFoundError):
    import pkg_resources

    dash_version_str = pkg_resources.get_distribution("dash").version
dash_version = version.parse(dash_version_str)


def dash_version_is_at_least(req_version: str = "1.12") -> bool:
    """Check that the used version of dash is greater or equal
    to some version `req_version`.

    Will return True if current dash version is greater than
    the argument "req_version".
    This is a private method, and should not be exposed to users.
    """
    return dash_version >= version.parse(req_version)


def retry(wait_time: float, max_time: float):
    """
    decorator to call a function until success

    Parameters
    ----------
    wait_time: numeric
        The wait time in seconds between trials
    max_time: numeric
        Maximum time to wait
    """

    def add_callback(function: _Callable) -> _Callable:
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            i = 1
            while True:
                try:
                    if i > 1:
                        logtxt = (
                            f"Trying to call function '{function.__name__}'! Trial #{i}."
                            + f" Used time: {time.time() - t0:.2}s",
                        )
                        logging.warning(logtxt)
                    out = function(*args, **kwargs)
                    break
                except Exception as e:
                    if time.time() - t0 > max_time:
                        raise e
                    else:
                        time.sleep(wait_time)
                finally:
                    i += 1
            return out

        return cast(_Callable, wrapper)

    return add_callback
