# Import DRF during model loading to verify configuration precedes DRF caches.
from rest_framework.throttling import SimpleRateThrottle  # noqa: F401
from rest_framework.views import APIView  # noqa: F401
