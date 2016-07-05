Welcome to Weasyl!
==================

.. highlight:: console

`Weasyl`_ is a social gallery website designed for artists, writers, musicians,
and more to share their work with other artists and fans. We seek to bring the
creative world together in one easy to use, friendly, community website.


Quickstart
----------

Weasyl runs within a `Docker`_ container. The ``wzl`` program drives management
of the system of Docker images. The only requirement is `Docker`_ 1.10 or
greater.

.. XXX: check version

The first steps are to set configuration to defaults and build all of the
images::

  $ ./wzl setup
  $ ./wzl build --all

Once the images are built, the development server can be started::

  $ ./wzl run

To access the development server, ``wzl`` can tell you where it's running::

  $ ./wzl url


Next Steps and Common Tasks
---------------------------

If it's the first time you've started Weasyl, you've recently pulled after a
few weeks, or you know there's been a schema change, you'll need to ensure the
database is using the most recent schema::

  $ ./wzl upgrade-db

Changes to python source files (any ``.py`` file) require a restart to be
reflected::

  $ ./wzl compose restart weasyl-app-dev

``weasyl-app-dev`` is the python application service. The URL should remain the
same across restarts.

Changes to nginx config require a restart as well, but for a different service::

  $ ./wzl compose restart nginx
  $ ./wzl url

Since the URL is pointed at nginx, and its port can change on boot, this will
likely mean there's a new URL.

Changes to stylesheets (any ``.sass`` file) require a rebuild of the generated
``.css`` files *and* a restart of the app server::

  $ ./wzl build -r assets-sass
  $ ./wzl compose restart weasyl-app-dev

If there's an error displayed, it's probably been logged. Logs can be streamed
live to your console as they happen::

  $ ./wzl logtail

Before you submit a pull request, make sure your new tests and all the old
tests are passing::

  $ ./wzl test

Underneath, orchestration is managed by ``docker-compose``\ [#docker_compose]_,
and since not all of its functionality has been re-exposed through ``wzl``,
``docker-compose`` itself is exposed as ``./wzl compose``. A few other useful
commands which are only accessible this way::

  $ ./wzl compose stop  # Shut down all services without destroying their state.
  $ ./wzl compose down  # Shut down all services and destroy persistent state.
  $ ./wzl compose ps  # Show what services are running.

.. [#docker_compose] `docker-compose <https://www.docker.com/products/docker-compose>`_
   won't need to be installed separately; ``wzl`` runs in its own container and
   installs its own dependencies.

Changes to the various ``Dockerfile``\ s or dependencies of the python code
will require the containers to be rebuilt. The slowest, but most reliable way
is to rebuild everything::

  $ ./wzl build --all

To instead rebuild a specific target's dependencies, and then that target::

  $ ./wzl build {target name}

Targets are listed in the help::

  $ ./wzl build --help

To build a specific target and then any target that depends on that specific
target (i.e. the reverse dependencies of a target)::

  $ ./wzl build -r {target name}


The Sample Database
-------------------

The downloaded database contains sample content pulled and scrubbed from
Weasyl staff accounts. No content should be included from non-staff users
or those who haven't otherwise explicitly given permission to use their
account.

For privacy and technical reasons, not all content is included: Hidden
submissions, private messages, journals, hidden favorites, notifications,
and similar things have been removed. If you want to develop around such
functionality, they will have to be added manually.

All passwords in the database have been set to 'password'.


Troubleshooting and Getting Help
--------------------------------

If you have questions or get stuck, you can trying talking to Weasyl project members in
the project's `gitter room <https://gitter.im/Weasyl/weasyl>`_.

The above instructions have been tested on Linux and OS X. Windows support is
currently in flux and incomplete.

Hopefully this isn't necessary, but there are also commands available to
inspect images and containers interactively for debugging::

  $ ./wzl attach weasyl-app-dev
  $ ./wzl shell weasyl-app-dev


Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_. By
participating in this project you agree to abide by its terms.

.. _Weasyl: https://www.weasyl.com
.. _Docker: https://www.docker.com/products/docker
.. _Contributor Code of Conduct: CODE_OF_CONDUCT.md
