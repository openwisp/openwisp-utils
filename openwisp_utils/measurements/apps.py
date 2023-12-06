from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class MeasurementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'openwisp_utils.measurements'
    app_label = 'openwisp_measurements'

    def ready(self):
        super().ready()
        self.connect_post_migrate_signal()

    def connect_post_migrate_signal(self):
        post_migrate.connect(self.post_migrate_receiver, sender=self)

    @classmethod
    def post_migrate_receiver(cls, **kwargs):
        if getattr(settings, 'DEBUG', False):
            # Do not send clean insights measurements in debug mode
            # i.e. when running tests.
            return

        from .tasks import send_clean_insights_measurements

        is_new_install = False
        if kwargs.get('plan'):
            migration, migration_rolled_back = kwargs['plan'][0]
            is_new_install = (
                migration_rolled_back is False
                and str(migration) == 'contenttypes.0001_initial'
            )

        if is_new_install:
            # This is a new installation
            send_clean_insights_measurements.delay()
        else:
            send_clean_insights_measurements.delay(upgrade_only=True)
