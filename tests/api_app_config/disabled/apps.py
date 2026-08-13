from openwisp_utils.api.apps import ApiAppConfig


class DisabledConfig(ApiAppConfig):
    name = "api_app_config.disabled"
    API_ENABLED = False
    REST_FRAMEWORK_SETTINGS = {
        "DEFAULT_THROTTLE_RATES": {"disabled": "30/minute"},
    }
