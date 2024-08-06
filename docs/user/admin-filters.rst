Admin Filters
=============

.. figure:: https://raw.githubusercontent.com/openwisp/openwisp-utils/media/docs/filter.gif
    :align: center

The ``admin_theme`` sub app provides an improved UI for the *changelist*
filter which occupies less space compared to the original implementation
in django: filters are displayed horizontally on the top (instead of
vertically on the side) and filter options are hidden in dropdown menus
which are expanded once clicked.

Multiple filters can be applied at same time with the help of "apply
filter" button. This button is only visible when total number of filters
is greater than 4. When filters in use are less or equal to 4 the "apply
filter" button is not visible and filters work like in the original django
implementation (as soon as a filter option is selected the filter is
applied and the page is reloaded).
