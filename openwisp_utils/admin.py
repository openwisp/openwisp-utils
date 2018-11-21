from django.contrib import admin
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class MultitenantAdminMixin(object):
    """
    Mixin that makes a ModelAdmin class multitenant:
    users will see only the objects related to the organizations
    they are associated with.
    """
    multitenant_shared_relations = []
    multitenant_parent = None

    def __init__(self, *args, **kwargs):
        super(MultitenantAdminMixin, self).__init__(*args, **kwargs)
        parent = self.multitenant_parent
        shared_relations = self.multitenant_shared_relations
        if parent and parent not in shared_relations:
            self.multitenant_shared_relations.append(parent)

    def get_repr(self, obj):
        return str(obj)

    get_repr.short_description = _('name')

    def get_queryset(self, request):
        """
        If current user is not superuser, show only the
        objects associated to organizations he/she is associated with
        """
        qs = super(MultitenantAdminMixin, self).get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        if hasattr(self.model, 'organization'):
            return qs.filter(organization__in=user.organizations_pk)
        elif not self.multitenant_parent:
            return qs
        else:
            qsarg = '{0}__organization__in'.format(self.multitenant_parent)
            return qs.filter(**{qsarg: user.organizations_pk})

    def _edit_form(self, request, form):
        """
        Modifies the form querysets as follows;
        if current user is not superuser:
            * show only relevant organizations
            * show only relations associated to relevant organizations
              or shared relations
        else show everything
        """
        fields = form.base_fields
        if not request.user.is_superuser:
            orgs_pk = request.user.organizations_pk
            # organizations relation;
            # may be readonly and not present in field list
            if 'organization' in fields:
                org_field = fields['organization']
                org_field.queryset = org_field.queryset.filter(pk__in=orgs_pk)
            # other relations
            q = Q(organization__in=orgs_pk) | Q(organization=None)
            for field_name in self.multitenant_shared_relations:
                # each relation may be readonly
                # and not present in field list
                if field_name not in fields:
                    continue
                field = fields[field_name]
                field.queryset = field.queryset.filter(q)

    def get_form(self, request, obj=None, **kwargs):
        form = super(MultitenantAdminMixin, self).get_form(request, obj, **kwargs)
        self._edit_form(request, form)
        return form

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(MultitenantAdminMixin, self).get_formset(request, obj=None, **kwargs)
        self._edit_form(request, formset.form)
        return formset


class MultitenantOrgFilter(admin.RelatedFieldListFilter):
    """
    Admin filter that shows only organizations the current
    user is associated with in its available choices
    """
    multitenant_lookup = 'pk__in'

    def field_choices(self, field, request, model_admin):
        if request.user.is_superuser:
            return super(MultitenantOrgFilter, self).field_choices(field, request, model_admin)
        organizations = request.user.organizations_pk
        return field.get_choices(include_blank=False,
                                 limit_choices_to={self.multitenant_lookup: organizations})


class MultitenantRelatedOrgFilter(MultitenantOrgFilter):
    """
    Admin filter that shows only objects which have a relation with
    one of the organizations the current user is associated with
    """
    multitenant_lookup = 'organization__in'


class TimeReadonlyAdminMixin(object):
    """
    mixin that automatically flags
    `created` and `modified` as readonly
    """
    def __init__(self, *args, **kwargs):
        self.readonly_fields += ('created', 'modified',)
        super(TimeReadonlyAdminMixin, self).__init__(*args, **kwargs)


class AlwaysHasChangedMixin(object):
    def has_changed(self):
        """
        This django-admin trick ensures the settings
        are saved even if default values are unchanged
        (without this trick new setting objects won't be
        created unless users change the default values)
        """
        if self.instance._state.adding:
            return True
        return super(AlwaysHasChangedMixin, self).has_changed()
