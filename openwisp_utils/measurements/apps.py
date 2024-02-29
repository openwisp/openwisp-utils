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
            # Do not send usage metrics in debug mode
            # i.e. when running tests.
            return

        from .tasks import send_usage_metrics

        is_new_install = False
        if kwargs.get('plan'):
            migration, migration_rolled_back = kwargs['plan'][0]
            is_new_install = (
                migration_rolled_back is False
                and str(migration) == 'contenttypes.0001_initial'
            )

        # If the migration plan includes creating table
        # for the ContentType model, then the installation is
        # treated as a new installation.
        if is_new_install:
            # This is a new installation
            send_usage_metrics.delay()
        else:
            send_usage_metrics.delay(upgrade_only=True)
