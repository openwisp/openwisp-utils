# Generated by Django 3.1.13 on 2021-11-30 09:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("test_project", "0003_project_operator_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="shelf",
            name="books_count",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Number of books"
            ),
        ),
        migrations.AddField(
            model_name="shelf",
            name="books_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("HORROR", "HORROR"),
                    ("FANTASY", "FANTASY"),
                    ("FACTUAL", "FACTUAL"),
                    ("Mystery", "Mystery"),
                    ("Historical Fiction", "Historical Fiction"),
                    ("Literary Fiction", "Literary Fiction"),
                    ("Romance", "Romance"),
                    ("Science Fiction", "Science Fiction"),
                    ("Short Stories", "Short Stories"),
                    ("Thrillers", "Thrillers"),
                    ("Biographies", "Biographies"),
                ],
                max_length=50,
                null=True,
                verbose_name="Type of book",
            ),
        ),
        migrations.AddField(
            model_name="shelf",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Create at"
            ),
        ),
        migrations.AddField(
            model_name="shelf",
            name="locked",
            field=models.BooleanField(default=True, verbose_name="Is locked"),
        ),
        migrations.AddField(
            model_name="shelf",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Owner of shelf",
            ),
        ),
    ]
