Welcome to libweasyl
====================

`libweasyl` is a library of functionality and database models that underpins
much of [weasyl](https://github.com/weasyl/weasyl) and its one-off scripts.


Setup
-----

To write a new tool using libweasyl (assuming you already have your database
setup and libweasyl's requirements installed in your python environment), you
probably should begin by setting up a call to [`configure_libweasyl()`]
(libweasyl/configuration.py). At minimum this will require a SQLAlchemy
`scoped_session` to your weasyl database and a staff dict identifying
the staff users.


Testing and Style Checks
------------------------

If you're making changes to libweasyl, you are expected to write unit tests
and to check your code for style mistakes.

Running unit tests:

    $ make test

Checking test coverage:

    $ make coverage

Style-checks:

    $ make check         # checks uncommitted changes. Runs pre-commit
    $ make check-all     # checks entire codebase
    $ make check-commit  # checks most recent commit
