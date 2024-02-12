from pathlib import Path

from typing import Union, Optional, TypeVar

try:
    from typing import Sequence, Callable
    from typing import Tuple
except ImportError:
    from collections.abc import Sequence, Callable
    from builtins import tuple as Tuple

import flask
import dash

from dash.exceptions import PreventUpdate
from dash.dependencies import Input, State, Output

import dash_uploader.settings as settings
from dash_uploader.uploadstatus import UploadStatus
from dash_uploader.utils import dash_version_is_at_least


T = TypeVar("T")
_Callable = TypeVar("_Callable", bound=Callable)


def _query_app_and_root(component_id: str) -> Tuple[Union[flask.Flask, dash.Dash], str]:
    """Query the app and the root folder by the given component id.

    This is a private method, and should not be exposed to users.
    """
    app_idx = settings.user_configs_query.get(component_id, None)
    if app_idx is None and settings.user_configs_default is not None:
        app_idx = settings.user_configs_default
    else:
        app_idx = 0
    app_item = settings.user_configs[app_idx]
    if not app_item["is_dash"]:
        raise TypeError(
            "The du.configure_upload must be called with a dash.Dash instance before "
            "the @du.callback can be used! Please configure the dash-uploader."
        )
    app = app_item["app"]
    upload_folder_root = app_item["upload_folder_root"]
    return app, upload_folder_root


def _create_dash_callback(callback: Callable[[UploadStatus], T], app_root_folder: str):
    """Wrap the dash callback the `upload_folder_root`.

    This function could be used as a wrapper. It will add the
    configurations of dash-uploader to the callback.
    """

    def wrapper(
        callbackbump: bool,
        uploaded_filenames: Sequence[str],
        total_files_count: int,
        uploaded_files_size: float,
        total_files_size: float,
        upload_id: Optional[str],
    ) -> T:
        if not callbackbump:
            raise PreventUpdate()

        uploadedfilepaths = []
        if uploaded_filenames is not None:
            if upload_id:
                root_folder = Path(app_root_folder) / upload_id
            else:
                root_folder = Path(app_root_folder)

            for filename in uploaded_filenames:
                file = root_folder / filename
                uploadedfilepaths.append(str(file))

        status = UploadStatus(
            uploaded_files=uploadedfilepaths,
            n_total=total_files_count,
            uploaded_size_mb=uploaded_files_size,
            total_size_mb=total_files_size,
            upload_id=upload_id,
        )
        return callback(status)

    return wrapper


def callback(
    output: Output,
    id: str = "dash-uploader",
    prevent_initial_call: Optional[bool] = None,
):
    """
    Add a callback to dash application.
    This callback fires when upload is completed.
    Note: Must be called after du.configure_upload!

    Parameters
    ----------
    output: dash Ouput
        The output dash component
    id: str
        The id of the du.Upload component.
    prevent_initial_call: bool
        The optional argument `prevent_initial_call`
        is supported since dash v1.12.0. When set
        True, it will cause the callback not to fire
        when its outputs are first added to the page.
        Defaults to `False` unless
        `prevent_initial_callbacks = True` at the
        app level.
        Compatibility:
        Only works for dash>=1.12.0. If the current
        dash is a pre-release version or an earlier
        version, this option would be ignored.

    Example
    -------
    @du.callback(
       output=Output('callback-output', 'children'),
       id='dash-uploader',
    )
    def get_a_list(filenames):
        return html.Ul([html.Li(filenames)])


    """

    app, upload_folder_root = _query_app_and_root(id)

    def add_callback(function: _Callable) -> _Callable:
        """
        Parameters
        ---------
        function: callable
            Function that receivers one argument,
            filenames and returns one argument,
            a dash component. The filenames is either
            None or list of str containing the uploaded
            file(s).
        output: dash.dependencies.Output
            The dash output. For example:
            Output('callback-output', 'children')

        """
        dash_callback = _create_dash_callback(
            function,
            upload_folder_root,
        )

        if not isinstance(app, dash.Dash):
            raise TypeError(
                "Try to define a callback for a non-dash app. The callback method "
                "should not be defined by this side. Please define the callback on the "
                "dashboard side, and let the dashboard connect to this cross-domain "
                "service."
            )

        kwargs = dict()
        if dash_version_is_at_least("1.12"):
            # See: https://github.com/plotly/dash/blob/dev/CHANGELOG.md  and
            #      https://community.plotly.com/t/dash-v1-12-0-release-pattern-matching-callbacks-fixes-shape-drawing-new-datatable-conditional-formatting-options-prevent-initial-call-and-more/38867
            # the `prevent_initial_call` option was added in Dash v.1.12
            kwargs["prevent_initial_call"] = (
                True if prevent_initial_call is None else bool(prevent_initial_call)
            )

        # Input: Change in the props will trigger callback.
        #     Whenever 'this.props.setProps' is called on the JS side,
        #     (dash specific special prop that is passed to every
        #     component of the dash app), a HTTP request is used to
        #     trigger a change in the property/attribute of a dash
        #     python component.
        # State: Pass along extra values without firing the callbacks.
        #
        # See also: https://dash.plotly.com/basic-callbacks
        dash_callback = app.callback(
            output,
            [Input(id, "dashAppCallbackBump")],
            [
                State(id, "uploadedFileNames"),
                State(id, "totalFilesCount"),
                State(id, "uploadedFilesSize"),
                State(id, "totalFilesSize"),
                State(id, "upload_id"),
            ],
            **kwargs
        )(dash_callback)

        return function

    return add_callback
