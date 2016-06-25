Some notes for myself surrounding this effort. Delete this file before
opening a pull request.

TODO
----

* Everything around web.ctx
  - One ugly way to do this is to use thread local request objects, but this isn't going to conform to pyramid best practices.
* Middleware setup still is missing a lot of features:
  - Add this middleware setup:
```
(DONE: Using a tween) app.add_processor(mw.cache_clear_processor)
(DONE: Using a tween that registers a property in define.py. Not thrilled with this one.) app.add_processor(mw.db_connection_processor)
(DONE: Using a tween. May have broken polecat due to how we're passing the request's args?) app.add_processor(mw.db_timer_processor(app))
(DONE: Kind of ugily with a tween and setting an attribute on the request) app.add_processor(mw.session_processor)
```
I bet these can all be set up trivially as a tween, except maybe for the session_processor which might be a session factory instead.
  - Set up mw.weasyl_exception_processor so that it gets exceptions. This can be passed as exceptionresponse_view when generating the configuration.
  - (DONE: I don't think this is necessary with pyramid's request object) Set up mw.endpoint_recording_delegate such that it gets endpoint names
  - (DONE) Make sure weasyl_404 works. Set it up with add_notfound_view.
  - (WONTFIX: Consider this later.) Setup a session_factory?

* Setup controllers
  - Because of how pyramid does routing with annotations rather than looking for `GET` and `POST` methods, the logic around controller_base.replace_methods() is likely to break
  - urls.py has changes to routes.py. It should be changed to set up a bunch of routes in the pyramid config
  - Add annotations to all of the controllers so that scan() finds them.
* Fix app.statFactory (DONE: Just stuck it in define. That's where everything else lives after all.)
  - `app` in general can go away. Just save the statFactory somewhere.
* I've removed the endpoint recording delegate. So uh handle that? (DONE: I think.)


Tests to do
-----------

Check all endpoints, mod tools, etc.
Check error messages for 404, permission exceeded, etc.
Throw an exception and confirm it looks right to sentry.