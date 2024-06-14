Database Backends
=================

.. include:: ../partials/developer-docs.rst

``openwisp_utils.db.backends.spatialite``
-----------------------------------------

This backend extends ``django.contrib.gis.db.backends.spatialite``
database backend to implement a workaround for handling `issue with sqlite
3.36 and spatialite 5 <https://code.djangoproject.com/ticket/32935>`_.
