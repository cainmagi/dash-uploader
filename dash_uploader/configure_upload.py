import logging

import dash
import flask

import dash_uploader.settings as settings
from dash_uploader.httprequesthandler import HttpRequestHandler
from dash_uploader.fixture import cross_domain


logger = logging.getLogger("dash_uploader")


def update_upload_api(requests_pathname_prefix, upload_api):
    """Path join for the API path name.
    This is a private method, and should not be exposed to users.
    """
    if requests_pathname_prefix == "/":
        return upload_api
    return "/".join(
        [
            requests_pathname_prefix.rstrip("/"),
            upload_api.lstrip("/"),
        ]
    )


def check_app(app):
    """Check the validity of the provided app.
    The app requires to be a dash.Dash instance or a flask.Flask
    instance. It should not be repeated in the user configurations.
    This is a private method, and should not be exposed to users.
    """
    is_dash = isinstance(app, dash.Dash)
    if not is_dash and not isinstance(app, flask.Flask):
        raise TypeError(
            'The argument "app" requires to be a dash.Dash instance or a flask.Flask instance.'
        )
    return is_dash


def check_upload_component_ids(upload_component_ids):
    """Check the validity of the component ids.
    This function is used for checking the validity of provided component
    ids. A valid id should be a non-empty str and not repeated in the
    configurations.
    This is a private method, and should not be exposed to users.
    """
    # When None, check the default configs.
    if upload_component_ids is None:
        if settings.user_configs_default is not None:
            raise ValueError(
                "The default app has been configured before. A repeated configuration is not allowed."
            )
        return None
    # When not None, check the ids first.
    valid_ids = None
    if isinstance(upload_component_ids, str) and upload_component_ids != "":
        valid_ids = (upload_component_ids,)
    if isinstance(upload_component_ids, (list, tuple)):
        if all(
            map(lambda uid: isinstance(uid, str) and uid != "", upload_component_ids)
        ):
            valid_ids = tuple(upload_component_ids)
    if valid_ids is None:
        raise TypeError(
            'The argument "upload_component_ids" should be None, str or [str].'
        )
    # Then, check the repetition of the provided ids.
    for uid in valid_ids:
        if uid in settings.user_configs_query:
            raise ValueError(
                'The component id "{0}" has been configured before. A repeated configuration is not allowed.'
            )
    return valid_ids


def check_remote_addr(remote_addr, upload_api):
    """Check the validity of the argument remote_addr.
    If this value is not None, it should be a non-empty str, and the
    argument "upload_api" requires to be None.
    This is a private method, and should not be exposed to users.
    """
    if remote_addr is None:
        return None
    if isinstance(remote_addr, str) and remote_addr != "":
        if upload_api is not None:
            raise TypeError(
                'The argument "upload_api" should be None when "remote_addr" is not None.'
            )
        return remote_addr
    raise TypeError('The argument "remote_addr" should be None or a non-empty str.')


def check_allowed_origins(allowed_origins):
    """Check the validity of the argument allowed_origins.
    A valid argument "allowed_origins" requires to be None, str or a
    sequence of str.
    This is a private method, and should not be exposed to users.
    """
    if allowed_origins is None:
        allowed_origins = settings.allowed_origins
    if isinstance(allowed_origins, str) and allowed_origins != "":
        return allowed_origins
    if isinstance(allowed_origins, (list, tuple)):
        if all(
            map(
                lambda origin: isinstance(origin, str) and origin != "", allowed_origins
            )
        ):
            allowed_origins = ", ".join(allowed_origins)
            return allowed_origins
    raise TypeError('The argument "allowed_origins" should be None, str or [str].')


def configure_upload(
    app,
    folder,
    use_upload_id=True,
    upload_api=None,
    remote_addr=None,
    allowed_origins=None,
    http_request_handler=None,
    upload_component_ids=None,
):
    r"""
    Configure the upload APIs for dash app.
    This function is required to be called before using du.callback.

    Parameters
    ---------
    app: dash.Dash or flask.Flask
        The application instance. It is required to be a dash.Dash
        for using du.callback.
    folder: str
        The folder where to upload files.
        Can be relative ("uploads") or
        absolute (r"C:\tmp\my_uploads").
        If the folder does not exist, it will
        be created automatically.
    use_upload_id: bool
        Determines if the uploads are put into
        folders defined by a "upload id" (upload_id).
        If True, uploads will be put into `folder`/<upload_id>/;
        that is, every user (for example with different
        session id) will use their own folder. If False,
        all files from all sessions are uploaded into
        same folder (not recommended).
    upload_api: None or str
        The upload api endpoint to use; the url that is used
        internally for the upload component POST and GET HTTP
        requests. For example: "/API/dash-uploader"
    remote_addr: None or str
        The full address of a remote server, including the IP, port and the
        upload_api.
        When this value is configured, the upload_api requires to be None.
        This argument should only be used for creating remote services, because
        no API would be configured locally when remote_addr is not None.
    allowed_origins: None or str or [str]
        The list of allowed origin(s) for the cross-domain access. If
        set '*', all domains would be allowed. If set None, would use
        du.settings to configure the origin(s).
    http_request_handler: None or class
        Used for custom configuration on the Http POST and GET requests.
        This can be used to add validation for the HTTP requests (Important
        if your site is public!). If None, dash_uploader.HttpRequestHandler is used.
        If you provide a class, use a subclass of HttpRequestHandler.
        See the documentation of dash_uploader.HttpRequestHandler for
        more details.
    upload_component_ids: None or str or [str]
        A list of du.Upload component ids. If set None, this configuration would be
        regarded as default configurations. If not, the registered app would be
        configured for the provided components.
    """
    # Check the validity of arguments.
    is_dash = check_app(app)
    upload_component_ids = check_upload_component_ids(upload_component_ids)
    allowed_origins = check_allowed_origins(allowed_origins)
    remote_addr = check_remote_addr(remote_addr, upload_api)

    # Configure the API. Extra configs are needed if using a proxy for dash app.
    if remote_addr is not None:  # upload_api is None in this case.
        service = remote_addr
    else:
        if upload_api is None:
            upload_api = settings.upload_api
        if is_dash and upload_api is not None:
            routes_pathname_prefix = app.config.get("routes_pathname_prefix", "/")
            requests_pathname_prefix = app.config.get("requests_pathname_prefix", "/")
            service = update_upload_api(requests_pathname_prefix, upload_api)
            full_upload_api = update_upload_api(routes_pathname_prefix, upload_api)
        else:
            service = upload_api
            full_upload_api = upload_api

    # Set the request handler.
    if http_request_handler is None:
        http_request_handler = HttpRequestHandler

    if remote_addr is None:  # Should not create APIs when given a remote remote_addr
        server = app.server if is_dash else app
        decorate_server(
            server,
            folder,
            full_upload_api,
            http_request_handler=http_request_handler,
            allowed_origins=allowed_origins,
            use_upload_id=use_upload_id,
        )

    # If no bugs are triggered, would update the user configs.
    # Set the upload api since du.Upload components
    # that are created after du.configure_upload
    # need to be able to read the api endpoint.
    app_idx = len(settings.user_configs)
    settings.user_configs.append(
        {
            "app": app,
            "service": service,
            "upload_api": upload_api,
            "upload_folder_root": folder,
            "is_dash": is_dash,
            "allowed_origins": allowed_origins,
            "upload_component_ids": upload_component_ids,
        }
    )
    # Set the query.
    if upload_component_ids is not None:
        for uid in upload_component_ids:
            settings.user_configs_query[uid] = app_idx
    else:
        settings.user_configs_default = app_idx


def decorate_server(
    server,
    temp_base,
    upload_api,
    http_request_handler,
    allowed_origins=None,
    use_upload_id=True,
):
    """
    Parameters
    ----------
    server: flask.Flask
        The flask server instance
    temp_base: str
        The upload root folder
    upload_api: str
        The upload api endpoint to use; the url that is used
        internally for the upload component POST and GET HTTP
        requests.
    allowed_origins: None or str or [str]
        The list of allowed origin(s) for the cross-domain access. If
        set '*', all domains would be allowed. If set None, would use
        du.settings to configure the origin(s).
    use_upload_id: bool
        Determines if the uploads are put into
        folders defined by a "upload id" (upload_id).
        If True, uploads will be put into `folder`/<upload_id>/;
        that is, every user (for example with different
        session id) will use their own folder. If False,
        all files from all sessions are uploaded into
        same folder (not recommended).
    """

    handler = http_request_handler(
        server, upload_folder=temp_base, use_upload_id=use_upload_id
    )

    def get(
        *args, **kwargs
    ):  # The two wrappers are required, because we need to modify the attributes of the function.
        return handler.get(*args, **kwargs)

    def post(*args, **kwargs):
        return handler.post(*args, **kwargs)

    end_point = upload_api.lstrip("/").replace("/", ".")
    server.add_url_rule(
        upload_api,
        end_point + ".get",
        cross_domain(methods=["GET"], origin=allowed_origins)(get),
        methods=["GET", "OPTIONS"],
    )
    server.add_url_rule(
        upload_api,
        end_point + ".post",
        cross_domain(methods=["POST"], origin=allowed_origins)(post),
        methods=["POST", "OPTIONS"],
    )
