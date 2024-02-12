from typing import Union, Optional

try:
    from typing import List, Tuple, Dict
except ImportError:
    from builtins import list as List, tuple as Tuple, dict as Dict
from typing_extensions import TypedDict

import dash
import flask


class UserConfig(TypedDict):
    """User-defined configurations.

    This configuration allows `dash-uploader` to be configured for multiple dash/flask
    applications simulateneously. This change will enable:
    - Serve dash uploader as flask services.
    - Configure multiple services, each service is used by one or more uploaders.

    The global variable `requests_pathname_prefix` and `routes_pathname_prefix` are
    moved into this configuration item.
    """

    app: Union[dash.Dash, flask.Flask]
    service: str
    upload_api: str
    routes_pathname_prefix: str
    requests_pathname_prefix: str
    upload_folder_root: str
    is_dash: bool
    allowed_origins: str
    upload_component_ids: Tuple[str, ...]


# The default upload api endpoint
# The du.configure_upload can change this
upload_api = "/API/dash-uploader"

# Default configurations for the cross-domain deployment
# The argument `allowed_origins` could be a string or a sequence. It defines
# a list of allowed origins for the cross-domain access. The configurations
# in the du.settings could be overrided by passing options of
# du.configure_upload_flask.
allowed_origins = "*"

# User configurations:
# The configuration list is used for storing user-defined configurations.
# Each item is set by an independent du.configure_upload. The list is
# formatted by `UserConfig`
#
# It is not recommended to change this dict manually. It should be
# automatically set by du.configure_upload.
user_configs: List[UserConfig] = list()

# Backward query dict:
# This dictionary is used for fast querying the items in user_configs. It
# is formatted as
# user_configs_query = {
#     'upload_id_1': list_index_1,
#     'upload_id_2': list_index_2,
#     ...
# }
# user_configs_query_default is an int (The index of the default config in
# user_configs.)
# It is not recommended to change this dict manually. It should be
# automatically set by du.configure_upload.
user_configs_query: Dict[str, int] = {}
user_configs_default: Optional[int] = None
