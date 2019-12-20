from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from openwisp_utils.base import TimeStampedEditableModel


class Shelf(TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False

    def clean(self):
        if self.name == "Intentional_Test_Fail":
            raise ValidationError('Intentional_Test_Fail')
        return self


class Book(TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)
    author = models.CharField(_('author'), max_length=64)
    shelf = models.ForeignKey('test_project.Shelf', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False


class RadiusAccounting(models.Model):
    id = models.BigAutoField(primary_key=True, db_column='radacctid')
    session_id = models.CharField(verbose_name=_('session ID'),
                                  max_length=64,
                                  db_column='acctsessionid',
                                  db_index=True)
    username = models.CharField(verbose_name=_('username'),
                                max_length=64,
                                db_index=True,
                                null=True,
                                blank=True)


class Project(models.Model):
    name = models.CharField(max_length=64,
                            null=True,
                            blank=True)

    def __str__(self):
        return self.name


class Operator(models.Model):
    first_name = models.CharField(max_length=30, default='test')
    last_name = models.CharField(max_length=30, default='test')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return self.first_name
