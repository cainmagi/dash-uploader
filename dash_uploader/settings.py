# The default upload api endpoint
# The du.configure_upload can change this
upload_api = "/API/resumable"

# Default configurations for the cross-domain deployment
# The argument `allowed_origins` could be a string or a sequence. It defines
# a list of allowed origins for the cross-domain access. The configurations
# in the du.settings could be overrided by passing options of
# du.configure_upload_flask.
allowed_origins = '*'

# User configurations:
# The configuration list is used for storing user-defined configurations.
# Each item is set by an independent du.configure_upload. The list is
# formatted as
# user_configs = {
#     {
#         'app': dash.Dash() or flask.Flask(),
#         'service': str,
#         'upload_api': str,
#         'routes_pathname_prefix': str,
#         'requests_pathname_prefix': str,
#         'upload_folder_root': str,
#         'is_dash': bool,
#         'allowed_origins': [str],
#         'upload_component_ids': [str]
#     },
#     ...
# }
# It is not recommended to change this dict manually. It should be
# automatically set by du.configure_upload.
user_configs = list()

# Backward query dict:
# This dictionary is used for fast querying the items in user_configs. It
# is formatted as
# user_configs_query = {
#     'upload_id_1': list_index_1,
#     'upload_id_2': list_index_2,
#     ...
# }
# user_configs_query is a str (The default name of the configs.)
# It is not recommended to change this dict manually. It should be
# automatically set by du.configure_upload.
user_configs_query = {}
user_configs_default = None
