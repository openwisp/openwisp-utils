from rest_framework.throttling import ScopedRateThrottle


class CustomScopedRateThrottle(ScopedRateThrottle):
    """
    Used only for automated testing purposes
    """

    pass
