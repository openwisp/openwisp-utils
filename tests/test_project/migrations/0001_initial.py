# Generated by Django 2.2.9 on 2019-12-20 17:20

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="RadiusAccounting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="radacctid", primary_key=True, serialize=False
                    ),
                ),
                (
                    "session_id",
                    models.CharField(
                        db_column="acctsessionid",
                        db_index=True,
                        max_length=64,
                        verbose_name="session ID",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        max_length=64,
                        null=True,
                        verbose_name="username",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Shelf",
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
                ("name", models.CharField(max_length=64, verbose_name="name")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="Operator",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("first_name", models.CharField(default="test", max_length=30)),
                ("last_name", models.CharField(default="test", max_length=30)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="test_project.Project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Book",
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
                ("name", models.CharField(max_length=64, verbose_name="name")),
                ("author", models.CharField(max_length=64, verbose_name="author")),
                (
                    "shelf",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="test_project.Shelf",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
