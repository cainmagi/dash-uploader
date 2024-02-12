import datetime

from typing import Union, TypeVar, cast

try:
    from typing import Sequence, Callable
except ImportError:
    from collections.abc import Sequence, Callable

from flask import current_app, make_response, request
from functools import wraps

import dash_uploader.settings as settings


_Callable = TypeVar("_Callable", bound=Callable)


def cross_domain(
    origin: Union[Sequence[str], str, None] = None,
    methods: Union[Sequence[str], str, None] = None,
    headers: Union[Sequence[str], str, None] = None,
    max_age: Union[int, datetime.timedelta] = 21600,
    attach_to_all: bool = True,
    automatic_options: bool = True,
):
    """
    A decorator for the cross-domain fixture.
    Modified by cainmagi@github
    This decorator is used for those APIs requiring the cross-domain
    access. Thanks for the work of rayitopy@stackoverflow
        https://stackoverflow.com/a/45054690

    Parameters
    ----------
    origin: str, or a sequence of str
        The allowed origin(s) from different domains. If set "*",
        all domains would be allowed. If set None, would use
        du.settings to configure the origin(s).
    methods: str, or a sequence of str
        The allowed methods of the cross-domain access. If set None,
        would use the default configuration of the flask.
    headers: str, or a sequence of str
        The header names that will be passed to the following header
        item of the response:
        "Access-Control-Allow-Headers"
        Specifing this value as "*" mean to allow all headers.
    max_age: int or datetime.timedelta
        The max age (seconds) of the cross-domain requests.
    attach_to_all: bool
        Whether to attach the cross-domain headers to all required
        methods. If set False, the headers would be only added to
        OPTIONS request.
    automatic_options: bool
        Whether to use the flask default OPTIONS response. If set
        False, users need to implement OPTIONS response.

    Example
    -------
    @app.route('/api/v1/user', methods=['OPTIONS', 'POST'])
    @crossdomain(origin="*")
    def add_user():
        pass

    """
    if methods is not None:
        if isinstance(methods, str):
            methods = [methods]
        methods = ", ".join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        _headers = ", ".join(x.upper() for x in headers)
    else:
        _headers = headers
    if origin is None:
        origin = settings.allowed_origins
    if not isinstance(origin, str):
        origin = ", ".join(origin)
    if isinstance(max_age, datetime.timedelta):
        max_age = max(1, int(max_age.total_seconds()))

    def get_methods() -> str:
        if methods is not None:
            return methods if isinstance(methods, str) else ", ".join(methods)

        options_resp = current_app.make_default_options_response()
        return options_resp.headers["allow"]

    def decorator(func: _Callable) -> _Callable:
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == "OPTIONS":
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(func(*args, **kwargs))
            if not attach_to_all and request.method != "OPTIONS":
                return resp

            h = resp.headers

            h["Access-Control-Allow-Origin"] = origin
            h["Access-Control-Allow-Methods"] = get_methods()
            h["Access-Control-Max-Age"] = str(max_age)
            if _headers is not None:
                h["Access-Control-Allow-Headers"] = _headers
            return resp

        func.provide_automatic_options = False
        setattr(wrapped_function, "provide_automatic_options", False)
        return cast(_Callable, wrapped_function)

    return decorator
