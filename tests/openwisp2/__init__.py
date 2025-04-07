from .celery import app as celery_app

__all__ = ["celery_app"]

# The following variables are set in ansible-openwisp2 and
# docker-openwisp appropriately. We only set them here for
# testing purpose.
__openwisp_version__ = "23.0.0a"
# The installation method can be one of "ansible" or "docker".
# We use "pip" only for testing.
__openwisp_installation_method__ = "pip"
