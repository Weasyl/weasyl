Welcome to Weasyl!
==================

.. highlight:: console

`Weasyl`_ is a social gallery website designed for artists, writers, musicians,
and more to share their work with other artists and fans. We seek to bring the
creative world together in one easy to use, friendly, community website.


Quickstart
----------

Weasyl runs within a `Docker`_ container. The ``wzl`` program manages the
system of Docker images. The only requirement is `Docker`_ 1.10 or greater.

The first steps are to set configuration to defaults, build all of the images,
and ensure the database schema is up to date::

  $ ./wzl setup
  $ ./wzl build --all
  $ ./wzl upgrade-db

Once this is done, the development server can be started::

  $ ./wzl run

To access the development server, ``wzl`` can tell you where it's running::

  $ ./wzl url


Next Steps and Common Tasks
---------------------------

- If you've recently pulled after a few weeks, or you know there's been a
  schema change, you'll need to ensure the database is using the most recent
  schema::

    $ ./wzl upgrade-db

- Changes to python source files (any ``.py`` file) require a restart to be
  reflected::

    $ ./wzl compose restart weasyl-app-dev

  ``weasyl-app-dev`` is the python application service. The URL should remain
  the same across restarts.

- Changes to nginx config require a restart as well, but for a different
  service::

    $ ./wzl compose restart nginx
    $ ./wzl url

  Since the URL is pointed at nginx, and its port can change on boot, this will
  likely mean there's a new URL.

- Changes to stylesheets (any ``.sass`` file) require a rebuild of the generated
  ``.css`` files *and* a restart of the app server::

    $ ./wzl build -r assets-sass
    $ ./wzl compose restart weasyl-app-dev

- If the web application indicates that there was an error, it's probably been
  logged. Logs can be streamed live to your console as they happen::

    $ ./wzl logtail

- Or, to run all of the services in the foreground, streaming logs to the
  console automatically::

    $ ./wzl run -n

  Note that this will run in the foreground until control-C is pressed, and
  then shut down all the services. ``./wzl logtail`` will not shut down
  services when control-C is pressed.

- Before you submit a pull request, make sure your new tests and all the old
  tests are passing::

    $ ./wzl test

- If you need direct access to ``docker-compose`` functionality, it's exposed
  as ``./wzl compose``. A few other useful commands which are currently only
  accessible this way::

    $ ./wzl compose stop  # Shut down all services without destroying their state.
    $ ./wzl compose down  # Shut down all services and destroy persistent state.
    $ ./wzl compose ps  # Show what services are running.

- Changes to the various ``Dockerfile``\ s or dependencies of the python code
  will require the containers to be rebuilt. The slowest, but most reliable way
  is to rebuild everything::

    $ ./wzl build --all

- To instead rebuild a specific target's dependencies, and then that target::

    $ ./wzl build {target name}

- To build a specific target and then any target that depends on that specific
  target (i.e. the reverse dependencies of a target)::

    $ ./wzl build -r {target name}

- After images have been rebuilt, services will have to be restarted::

    $ ./wzl run

  While ``./wzl run`` is usually smart about figuring out which services need
  to be restarted, it's sometimes necessary to restart services individually by
  name::

    $ ./wzl compose restart {service name}

  Or, to restart everything unconditionally::

    $ ./wzl compose restart


Targets
~~~~~~~

All of the ``Dockerfile``\ s for these targets are in the ``docker`` directory
under the repository root. Details beyond the ``Dockerfile`` are specified in
``docker-compose.yml``, ``docker-compose-build.yml``, or ``_wzl/wzl.py``.

``weasyl-base``
  The base image on which all other ``weasyl-*`` images are built. This is
  basically just `Ubuntu Xenial <http://releases.ubuntu.com/16.04/>`_ with a
  few packages installed via ``apt``.

``weasyl-build``
  The base image for doing build-related tasks against the source tree, such as
  creating wheels which will be installed into the app images.

``weasyl-build-dev-wheels``
  A non-image target which builds all of the wheels for ``weasyl`` and
  ``libweasyl``, as well as wheels for development-time dependencies like for
  running tests or building docs.

``weasyl-app``
  The image for running the python application server without having any of the
  source tree mounted as a volume.

``weasyl-app-dev`` [#service]_
  The image for running the python application server using the local source
  tree in addition to code installed from the wheelhouse.

``cache`` [#service]_
  The image for memcached.

``db`` [#service]_
  The image for the postgres database server. The sample database referenced
  below will be fetched when a container starts from this image for the first
  time, not when the container is built.

``nginx`` [#service]_
  The image for the nginx front-end HTTP proxy.

``assets``
  The image for building the static assets. Currently, this is only
  stylesheets, but might include javascript in the future.

``assets-sass``
  A non-image target that will compile Sass stylesheets into ``.css`` files.

The difference between ``weasyl-app`` and ``weasyl-app-dev`` is intended to be
no more than convenience: without having the local source tree mounted in the
container, the latency between "make a code change" and "view the code change
locally" would increase.

.. [#service] These targets are also services.


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

There are also commands available to inspect images and running services
interactively for debugging::

  $ ./wzl attach {service name}
  $ ./wzl shell {image name}


Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_. By
participating in this project you agree to abide by its terms.

.. _Weasyl: https://www.weasyl.com
.. _Docker: https://www.docker.com/products/docker
.. _Contributor Code of Conduct: CODE_OF_CONDUCT.md
