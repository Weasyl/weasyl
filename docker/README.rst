Targets
=======

All of the ``Dockerfile``\ s for these targets are in this directory. Details
beyond the ``Dockerfile`` are specified in the parent directory in
``docker-compose.yml``, ``docker-compose-build.yml``, or ``_wzl/wzl.py``.

Services are denoted with a *(service)* suffix, which are the images that
``docker-compose`` manages by bringing containers up and down as necessary.

``weasyl-base``
  The base image on which all other ``weasyl-*`` images are built. This is
  basically just `Alpine Linux 3.5 <https://alpinelinux.org>`_ with a
  few packages installed via ``apk``.

``weasyl-build``
  The base image for doing build-related tasks against the source tree, such as
  creating wheels which will be installed into the app images and
  compiling packages installed via ``npm``.

``weasyl-build-dev-wheels``
  A non-image target which builds all of the wheels for ``weasyl`` and
  ``libweasyl``, as well as wheels for development-time dependencies like for
  running tests or building docs.

``weasyl-app``
  The image for running the python application server without having any of the
  source tree mounted as a volume.

``weasyl-app-dev`` (service)
  The image for running the python application server using the local source
  tree in addition to code installed from the wheelhouse.

``weasyl-assets``
  The image for building the static assets. Currently, this is only
  stylesheets, but might include javascript in the future.

``weasyl-assets-sass``
  A non-image target that will compile Sass stylesheets into ``.css`` files.

``cache`` (service)
  The image for memcached.

``db`` (service)
  The image for the postgres database server. The sample database referenced
  below will be fetched when a container starts from this image for the first
  time, not when the container is built. The ``wzl`` build of ``db`` will also
  automatically run ``upgrade-db``.

``nginx`` (service)
  The image for the nginx front-end HTTP proxy.

The difference between ``weasyl-app`` and ``weasyl-app-dev`` is intended to be
no more than convenience: without having the local source tree mounted in the
container, the latency between "make a code change" and "view the code change
locally" would increase.
