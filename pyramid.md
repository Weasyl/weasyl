Some notes for myself surrounding this effort. Delete this file before
opening a pull request.

TODO
----

* Everything around web.ctx
  - One ugly way to do this is to use thread local request objects, but this isn't going to conform to pyramid best practices.
* (DONE) Middleware setup still is missing a lot of features:
  - Add this middleware setup:
```
(DONE: Using a tween) app.add_processor(mw.cache_clear_processor)
(DONE: Using a tween that registers a property in define.py. Not thrilled with this one. UPDATE: Now uses reified properties instead) app.add_processor(mw.db_connection_processor)
(DONE: Using a tween. May have broken polecat due to how we're passing the request's args?) app.add_processor(mw.db_timer_processor(app))
(DONE: Kind of ugily with a tween and setting an attribute on the request) app.add_processor(mw.session_processor)
```
I bet these can all be set up trivially as a tween, except maybe for the session_processor which might be a session factory instead.
  - (DONE. Although I registered a view with a context of `Exception` rather than setting up exceptionresponse_view) Set up mw.weasyl_exception_processor so that it gets exceptions. This can be passed as exceptionresponse_view when generating the configuration.
  - (DONE: I don't think this is necessary with pyramid's request object) Set up mw.endpoint_recording_delegate such that it gets endpoint names
  - (DONE) Make sure weasyl_404 works. Set it up with add_notfound_view.
  - (WONTFIX: Consider this later.) Setup a session_factory?

* Setup controllers
  - Because of how pyramid does routing with annotations rather than looking for `GET` and `POST` methods, the logic around controller_base.replace_methods() is likely to break
  - urls.py has changes to routes.py. It should be changed to set up a bunch of routes in the pyramid config
  - Add annotations to all of the controllers so that scan() finds them. Or set up all the routes in one call.
* (DONE: Just stuck it in define. That's where everything else lives after all.) Fix app.statFactory
  - `app` in general can go away. Just save the statFactory somewhere.
* (DONE: I think.) I've removed the endpoint recording delegate. So uh handle that?

* several places in api.py need to be updated with pyramid style response codes.

* oauth2.py is also basically a controller despite not being in the controller path and will need an update.

* (DONE: There's an issue in that exceptions thrown before request.weasyl_session is set will not be handled correctly) I'm not sure the exception handler will do the expected thing if we get an exception in tween code. As such consider making it a tween itself instead (closer to the original design)

* define.py's use of config._in_test is almost certainly wrong.

* (DONE: Sort of. Have request.web_input() to replicate old web.input() behavior) Come up with the proper idiom for default form values.
  - .setdefault() isn't great because it's order sensitive.
  - .get(k, default) is a bit verbose to use.

* test that cookies are cleared correctly, especially WZL session numbers, etc.

* (DONE) Try to replace define.get_userid() with a reified request.userid property.

* flake8 everything before merge request.
* check test coverage before merge request.

Tests to do
-----------

I haven't tested signup yet. That should be done.
Check all endpoints, mod tools, etc.
Check error messages for 404, permission exceeded, etc.
Throw an exception and confirm it looks right to sentry.
Double check that 404 and 403 are being respected specially.
Check the output of absolutifying URLs. This was changed somewhat.


Stretch goals
-------------

* Consider adding pyramid's built in debugging tween for 500 errors. Only enable it for dev, not prod.


Future Work
-----------

* Constructing Response()s everywhere is probably silly: We could just return webpage text with a renderer of string. This would likely be cleaner and avoid most of the issues around losing changes to request.response.
* Clean up use of log_exc(). This should really just be a define.log_exc() universally probably.
* Refactor to get rid of the new define.get_weasyl_session() call. It was created to handle a few places (such as signin) where non-view code manipulates the session directly.
* Handle exceptions thrown prior to the setting of request.weasyl_session
* Rename weasyl.controllers to `weasyl.views`. Wait till after the merge just in case it confuses github.