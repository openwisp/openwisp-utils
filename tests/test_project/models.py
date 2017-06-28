from django.db import models
from django.utils.translation import ugettext_lazy as _
from openwisp_users.mixins import OrgMixin
from openwisp_utils.base import TimeStampedEditableModel


class Shelf(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        abstract = False


class Book(OrgMixin, TimeStampedEditableModel):
    name = models.CharField(_('name'), max_length=64)
    author = models.CharField(_('author'), max_length=64)
    shelf = models.ForeignKey('test_project.Shelf')

    def __str__(self):
        return self.name

    class Meta:
        abstract = False
