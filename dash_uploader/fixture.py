import datetime

from typing import Union, TypeVar, cast

try:
    from typing import Sequence, Callable
except ImportError:
    from collections.abc import Sequence, Callable

import flask.views
from flask import current_app, make_response, request
from functools import wraps

from . import settings


_Callable = TypeVar("_Callable", bound=Callable)
_Response = TypeVar("_Response", bound=flask.Response)


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

    def configure_resp(resp: _Response) -> _Response:
        h = resp.headers
        h["Access-Control-Allow-Origin"] = origin
        h["Access-Control-Allow-Methods"] = get_methods()
        h["Access-Control-Max-Age"] = str(max_age)
        if _headers is not None:
            h["Access-Control-Allow-Headers"] = _headers
        return resp

    def decorator(func: _Callable) -> _Callable:
        if isinstance(func, type) and issubclass(func, flask.views.View):

            if issubclass(func, flask.views.MethodView):

                def wrap_plain(_func):
                    @wraps(_func)
                    def _wrapped(*args, **kwargs):
                        resp = make_response(_func(*args, **kwargs))
                        if not attach_to_all and request.method != "OPTIONS":
                            return resp
                        return configure_resp(resp)

                    return _wrapped

                func_sub_methods = dict()
                for m_name in ("get", "post"):
                    mtd = getattr(func, m_name, None)
                    if mtd is not None:
                        func_sub_methods[m_name] = wrap_plain(mtd)

                if automatic_options:

                    def method_option(self):
                        resp = current_app.make_default_options_response()
                        return configure_resp(resp)

                    func_sub_methods["options"] = method_option

                func_sub = type(func.__name__, (func,), func_sub_methods)
                return cast(_Callable, func_sub)

            else:

                def wrap_dispatch(_func):
                    @wraps(_func)
                    def _wrapped(*args, **kwargs):
                        if automatic_options and request.method == "OPTIONS":
                            resp = current_app.make_default_options_response()
                        else:
                            resp = make_response(_func(*args, **kwargs))
                        if not attach_to_all and request.method != "OPTIONS":
                            return resp
                        return configure_resp(resp)

                    return _wrapped

                func_sub_methods = dict()
                mtd = getattr(func, "dispatch_request", None)
                if mtd is not None:
                    func_sub_methods["dispatch_request"] = wrap_dispatch(mtd)
                else:

                    def _dispatch_request(self): ...

                    func_sub_methods["dispatch_request"] = wrap_dispatch(
                        _dispatch_request
                    )
                func_sub = type(func.__name__, (func,), func_sub_methods)
                return cast(_Callable, func_sub)

        elif callable(func):

            @wraps(func)
            def wrapped_function(*args, **kwargs):
                if automatic_options and request.method == "OPTIONS":
                    resp = current_app.make_default_options_response()
                else:
                    resp = make_response(func(*args, **kwargs))
                if not attach_to_all and request.method != "OPTIONS":
                    return resp
                return configure_resp(resp)

            func.provide_automatic_options = False
            setattr(wrapped_function, "provide_automatic_options", False)
            return cast(_Callable, wrapped_function)

        else:
            raise TypeError(
                "Cannot recognized the value to be decorated. It needs to "
                "be a `flask.view` or a function."
            )

    return decorator
