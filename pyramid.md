Some notes for myself surrounding this effort. Delete this file before
opening a pull request.

TODO
----

* Figure out a better home for app.statsFactory.
* Everything around web.ctx
  - One ugly way to do this is to use thread local request objects, but this isn't going to conform to pyramid best practices.
* Middleware setup still is missing a lot of features:
  - Add this middleware setup:
```
app.add_processor(mw.cache_clear_processor)
app.add_processor(mw.db_connection_processor)
app.add_processor(mw.db_timer_processor(app))
app.add_processor(mw.session_processor)
```
I bet these can all be set up trivially as a tween, except maybe for the session_processor which might be a session factory instead.
  - Set up mw.weasyl_exception_processor so that it gets exceptions. This can be passed as exceptionresponse_view when generating the configuration.
  - Set up mw.endpoint_recording_delegate such that it gets endpoint names
  - Make sure weasyl_404 works. Set it up with add_notfound_view.
  - Setup a session_factory?
* Setup controllers
  - Because of how pyramid does routing with annotations rather than looking for `GET` and `POST` methods, the logic around controller_base.replace_methods() is likely to break
  - urls.py has changes to routes.py. It should be changed to set up a bunch of routes in the pyramid config
  - Add annotations to all of the controllers so that scan() finds them.
