SECRET_KEY = "test"
TESTING = True

INSTALLED_APPS = [
    "api_app_config.first.apps.FirstConfig",
    "rest_framework",
    "api_app_config.second.apps.SecondConfig",
    "api_app_config.disabled.apps.DisabledConfig",
]

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {"first": "99/minute"},
}
