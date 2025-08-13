Collection of Usage Metrics
===========================

The ``openwisp-utils`` module includes an optional sub-app
``openwisp_utils.metric_collection``, which allows us to collect of the
following information from OpenWISP instances:

- OpenWISP Version
- List of enabled OpenWISP modules and their version
- Operating System identifier, e.g.: Linux version, Kernel version, target
  platform (e.g. x86)
- Installation method, if available, e.g. :doc:`ansible-openwisp2
  </ansible/index>` or :doc:`docker-openwisp </docker/index>`

The data above is collected during the following events:

- **Install**: when OpenWISP is installed the first time
- **Upgrade**: when any OpenWISP module is upgraded
- **Heartbeat**: once every 24 hours

We collect data on OpenWISP usage to gauge user engagement, satisfaction,
and upgrade patterns. This informs our development decisions, ensuring
continuous improvement aligned with user needs.

To enhance our understanding and management of this data, we have
integrated `Clean Insights <https://cleaninsights.org/>`_, a
privacy-preserving analytics tool. Clean Insights allows us to responsibly
gather and analyze usage metrics without compromising user privacy. It
provides us with the means to make data-driven decisions while respecting
our users' rights and trust.

We have taken great care to ensure no sensitive or personal data is being
tracked.

Opting Out from Metric Collection
---------------------------------

You can opt-out from sharing this data any time from the "System Info"
page.

.. note::

    When a user opts out of metric collection through the web interface, a
    one-time metric is still sent to record the opt-out event. This helps
    distinguish between user abandonment and intentional opt-outs.

Alternatively, you can also remove the
``openwisp_utils.metric_collection`` app from ``INSTALLED_APPS`` in one of
the following ways:

- If you are using the :doc:`ansible-openwisp2 </ansible/index>` role, you
  can set the variable ``openwisp2_usage_metric_collection`` to ``false``
  in your playbook.
- If you are using :doc:`docker-openwisp </docker/index>`, you can set set
  the environment variable ``METRIC_COLLECTION`` to ``False`` in the
  ``.env`` file.

However, **it would be very helpful to the project if you keep the
colection of these metrics enabled**, because the feedback we get from
this data is useful to guide the project in the right direction.
