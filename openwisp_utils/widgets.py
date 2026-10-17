from django.conf import settings
from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
from django.forms import Media, Select
from django.utils.translation import get_language


class Select2Widget(Select):
    """Select2 autocomplete widget for Django ChoiceFields."""

    @property
    def media(self):
        extra = "" if getattr(settings, "DEBUG", False) else ".min"
        i18n_name = SELECT2_TRANSLATIONS.get(get_language())
        i18n_file = (
            ("admin/js/vendor/select2/i18n/{0}.js".format(i18n_name),)
            if i18n_name
            else ()
        )
        return Media(
            js=(
                "admin/js/vendor/jquery/jquery{0}.js".format(extra),
                "admin/js/vendor/select2/select2.full{0}.js".format(extra),
            )
            + i18n_file
            + ("admin/js/jquery.init.js", "openwisp-utils/js/select2.js"),
            css={
                "screen": ("admin/css/vendor/select2/select2{0}.css".format(extra),),
            },
        )

    def __init__(self, attrs=None, choices=()):
        attrs = attrs or {}
        attrs["class"] = "ow-select2 {0}".format(attrs.get("class", "")).strip()
        super().__init__(attrs, choices)
