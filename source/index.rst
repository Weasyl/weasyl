Weasyl HTTP API
===============


Basic
-----


.. http:get:: /api/version(.format)

   The current version of Weasyl, in some specified format. The format can be
   one of ``.json`` or ``.txt``, or omitted for JSON by default. For example::

     {"short_sha": "deadbeef"}


.. http:get:: /api/whoami

   The currently logged-in user, as JSON. For example::

     {"login": "weykent", "userid": 5756}

   If there is no current user, the result will be::

     {"login": null, "userid": 0}
