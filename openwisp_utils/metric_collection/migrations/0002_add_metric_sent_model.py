# Generated manually for adding MetricSent model

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("metric_collection", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetricSent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        help_text="Type of metric (Install, Heartbeat, Upgrade, Consent Withdrawn)",
                        max_length=50,
                    ),
                ),
                (
                    "metrics_hash",
                    models.CharField(
                        help_text="SHA-256 hash of the metrics payload",
                        max_length=64,
                    ),
                ),
                (
                    "date",
                    models.DateField(help_text="Date when the metric was sent"),
                ),
            ],
            options={
                "verbose_name": "Sent Metric",
                "verbose_name_plural": "Sent Metrics",
                "ordering": ("-created",),
                "unique_together": {("category", "metrics_hash", "date")},
            },
        ),
    ]