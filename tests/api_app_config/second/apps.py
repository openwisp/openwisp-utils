from openwisp_utils.api.apps import ApiAppConfig


class SecondConfig(ApiAppConfig):
    name = "api_app_config.second"
    API_ENABLED = True
    REST_FRAMEWORK_SETTINGS = {
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_THROTTLE_RATES": {"second": "20/minute"},
    }
