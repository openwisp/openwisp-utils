from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from openwisp_utils.base import KeyField, TimeStampedEditableModel, UUIDModel
from openwisp_utils.fields import (
    FallbackBooleanChoiceField,
    FallbackCharChoiceField,
    FallbackCharField,
    FallbackDecimalField,
    FallbackPositiveIntegerField,
    FallbackTextField,
    FallbackURLField,
)


class Shelf(TimeStampedEditableModel):
    TYPES = (
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
    )
    name = models.CharField(_("name"), max_length=64)
    books_type = models.CharField(
        _("Type of book"), choices=TYPES, null=True, blank=True, max_length=50
    )
    books_count = FallbackPositiveIntegerField(
        fallback=21,
        verbose_name=_("Number of books"),
    )
    locked = models.BooleanField(_("Is locked"), default=True)
    owner = models.ForeignKey(
        "auth.User",
        blank=True,
        null=True,
        verbose_name=_("Owner of shelf"),
        on_delete=models.CASCADE,
    )
    writers = models.ManyToManyField(
        "auth.User",
        blank=True,
        verbose_name=_("Writers"),
        related_name="writer_of",
    )
    created_at = models.DateTimeField(
        _("Create at"), null=True, blank=True, auto_now_add=True
    )

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

    def clean(self):
        if self.name == "Intentional_Test_Fail":
            raise ValidationError("Intentional_Test_Fail")
        return self


class Book(TimeStampedEditableModel):
    name = models.CharField(_("name"), max_length=64)
    author = models.CharField(_("author"), max_length=64)
    shelf = models.ForeignKey("test_project.Shelf", on_delete=models.CASCADE)
    price = FallbackDecimalField(max_digits=4, decimal_places=2, fallback=20.0)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False


class RadiusAccounting(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="radacctid")
    session_id = models.CharField(
        verbose_name=_("session ID"),
        max_length=64,
        db_column="acctsessionid",
        db_index=True,
    )
    username = models.CharField(
        verbose_name=_("username"), max_length=64, db_index=True, null=True, blank=True
    )
    start_time = models.DateTimeField(
        verbose_name=_("start time"),
        null=True,
        blank=True,
    )
    stop_time = models.DateTimeField(
        verbose_name=_("stop time"),
        null=True,
        blank=True,
    )


class OrganizationRadiusSettings(models.Model):
    is_active = FallbackBooleanChoiceField(
        fallback=False,
    )
    is_first_name_required = FallbackCharChoiceField(
        max_length=32,
        choices=(
            ("disabled", _("Disabled")),
            ("allowed", _("Allowed")),
            ("mandatory", _("Mandatory")),
        ),
        fallback="disabled",
    )
    greeting_text = FallbackCharField(
        max_length=200,
        fallback="Welcome to OpenWISP!",
    )
    password_reset_url = FallbackURLField(
        max_length=200,
        fallback="http://localhost:8000/admin/password_change/",
    )
    extra_config = FallbackTextField(
        max_length=200,
        fallback="no data",
    )


class Project(UUIDModel):
    name = models.CharField(max_length=64, null=True, blank=True)
    key = KeyField(unique=True, db_index=True, help_text=_("unique project key"))

    def __str__(self):
        return self.name


class Operator(models.Model):
    first_name = models.CharField(max_length=30, default="test")
    last_name = models.CharField(max_length=30, default="test")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.first_name
