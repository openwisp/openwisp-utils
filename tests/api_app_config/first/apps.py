from openwisp_utils.api.apps import ApiAppConfig


class FirstConfig(ApiAppConfig):
    name = "api_app_config.first"
    API_ENABLED = True
    REST_FRAMEWORK_SETTINGS = {
        "DEFAULT_THROTTLE_RATES": {"first": "10/minute"},
    }
