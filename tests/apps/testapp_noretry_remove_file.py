import uuid

import dash_uploader as du
import dash

if du.utils.dash_version_is_at_least("2.0.0"):
    from dash import html  # if dash <= 2.0.0, use: import dash_html_components as html
else:
    import dash_html_components as html

from dash.dependencies import Output
from dash_uploader.httprequesthandler import HttpRequestHandler, remove_file

UPLOAD_FOLDER_ROOT = R"C:\tmp\Uploads"
app = dash.Dash(__name__)

# A special version of HttpRequestHandler where
# there are *no retries* in the remove file function
# This is used in tests to generate an error message to user
# faster.


class HttpRequestHandlerWithoutFileRetries(HttpRequestHandler):
    remove_file = staticmethod(remove_file)


du.configure_upload(
    app, UPLOAD_FOLDER_ROOT, http_request_handler=HttpRequestHandlerWithoutFileRetries
)


def get_upload_component(id):
    return du.Upload(
        id=id,
        text="Drag and Drop files here",
        text_completed="Completed: ",
        cancel_button=True,
        pause_button=True,
        # max_file_size=130,  # 130 Mb
        # max_total_size=350,
        # filetypes=["csv", "zip"],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=10,
    )


def get_app_layout():

    return html.Div(
        [
            html.H1("Demo"),
            html.Div(
                [
                    get_upload_component(id="dash-uploader"),
                    html.Div(id="callback-output"),
                ],
                style={  # wrapper div style
                    "textAlign": "center",
                    "width": "600px",
                    "padding": "10px",
                    "display": "inline-block",
                },
            ),
        ],
        style={
            "textAlign": "center",
        },
    )


# get_app_layout is a function
# This way we can use unique session id's as upload_id's
app.layout = get_app_layout


# 3) Create a callback
@du.callback(
    output=Output("callback-output", "children"),
    id="dash-uploader",
)
def callback_on_completion(status: du.UploadStatus):
    print(status)
    return html.Ul([html.Li(str(x)) for x in status["uploaded_files"]])


if __name__ == "__main__":
    app.run_server(debug=True)
