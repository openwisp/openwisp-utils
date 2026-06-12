import logging

from django import template
from django.template.defaultfilters import stringfilter
from django.template.loader import get_template
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)
register = template.Library()


def _render_single_filter(cl, spec, total_filters, has_sub_filters=False):
    tpl = get_template(spec.template)
    choices = list(spec.choices(cl))
    selected_choice = None
    for choice in choices:
        if choice["selected"]:
            selected_choice = choice["display"]
    return tpl.render(
        {
            "title": spec.title,
            "choices": choices,
            "spec": spec,
            "show_button": total_filters > 4 or has_sub_filters,
            "selected_choice": selected_choice,
        }
    )


@register.simple_tag
def ow_create_filter(cl, spec, total_filters):
    return _render_single_filter(cl, spec, total_filters)


@register.simple_tag
def ow_render_filters(cl, filter_specs):
    """Render filter specs, grouping parent and sub-filters together.

    Parent filters are wrapped with their sub-filters in a
    ``.ow-filter-group`` container so the sub-filter renders vertically
    below the parent inside an ``.ow-sub-filter-group``.
    """
    specs = list(filter_specs)

    # Separate parent filters and sub-filters
    parent_filters = []
    sub_filters = []
    for spec in specs:
        if getattr(spec, "parent_parameter_name", None) is not None:
            sub_filters.append(spec)
        else:
            parent_filters.append(spec)
    # Sub-filters should not count toward total_filters since they are
    # normally hidden and don't affect the layout decision for the Apply button
    total_filters = len(parent_filters)
    # Discover relationships
    parent_to_children = {parent: [] for parent in parent_filters}
    consumed_sub_filters = set()
    for parent in parent_filters:
        expected_params = parent.expected_parameters()
        for child in sub_filters:
            if child in consumed_sub_filters:
                continue
            parent_param = getattr(child, "parent_parameter_name")
            if any(
                p == parent_param or p.startswith(parent_param + "__")
                for p in expected_params
            ):
                parent_to_children[parent].append(child)
                consumed_sub_filters.add(child)
    # Handle orphaned sub-filters (those that could not be matched with any parent)
    for child in sub_filters:
        if child not in consumed_sub_filters:
            logger.error(
                "Orphaned sub-filter detected: %s with parent_parameter_name='%s'",
                child.__class__.__name__,
                getattr(child, "parent_parameter_name", None),
            )
    # Render filters
    has_sub_filters = len(sub_filters) > 0
    output = []
    for parent in parent_filters:
        children = parent_to_children[parent]
        if children:
            output.append('<div class="ow-filter-group">')
            output.append(
                _render_single_filter(cl, parent, total_filters, has_sub_filters)
            )
            output.append('<div class="ow-sub-filter-group">')
            for child in children:
                output.append(
                    _render_single_filter(cl, child, total_filters, has_sub_filters)
                )
            output.append("</div>")
            output.append("</div>")
        else:
            output.append(
                _render_single_filter(cl, parent, total_filters, has_sub_filters)
            )
    return mark_safe("".join(output))


@register.filter
def has_sub_filters(filter_specs):
    """Check if any filter spec is a sub-filter."""
    for spec in filter_specs:
        if getattr(spec, "parent_parameter_name", None) is not None:
            return True
    return False


@register.filter
@stringfilter
def join_string(value):
    """Can be used to join strings with "-" to make id or class."""
    return value.lower().replace(" ", "-")
