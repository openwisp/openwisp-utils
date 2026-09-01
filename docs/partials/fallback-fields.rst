.. note::

    - The field will return the **fallback value** whenever is set to
      ``None``.
    - Setting the same value as the **fallback value** will save ``None``
      (NULL) in the database.
    - Fallback values are live runtime configuration and must be
      considered unavailable on historical models used in data migrations.
      Data migrations must use explicit values instead of relying on
      fallback behavior.
