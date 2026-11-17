Weasyl HTTP API
===============


Basic endpoints
---------------


.. http:get:: /api/version(.format)

   The current version of Weasyl, in some specified format. The format can be
   one of ``.json`` or ``.txt``, or omitted for JSON by default. For example::

     {"short_sha": "deadbeef"}


.. http:get:: /api/whoami

   The currently logged-in user, as JSON. For example::

     {"login": "weykent", "userid": 5756}

   If there is no current user, the response will be a :http:statuscode:`401`.


.. http:get:: /api/useravatar

   A user's avatar.

   :query username: The user's :term:`login name`.

   The result will resemble::

     {"avatar": "https://www.weasyl.com/static/user/66/42/8d/0a/3f/8c/5756/avatar.png"}

   Users without an avatar will get the default avatar icon back.


.. http:get:: /api/submissions/frontpage

   A list of submissions from the front page, respecting the current user's
   browsing settings.

   :query since: An :term:`ISO 8601 timestamp`. If specified, only submissions
      posted after this time will be returned.

   :query count: If specified, no more than this many submissions will be
      returned.

   This will return at most 100 submissions. If *count* is more than 100, at
   most 100 submissions will be returned. It is possible to receive less than
   *count* submissions back if too many submissions are filtered by the user's
   e.g. tag filters.

   The result will be a JSON array of :ref:`submission objects <submissions>`.


.. http:get:: /api/submissions/(submitid)/view

   View a particular submission by its ``submitid``.

   :query anyway: If omitted, the current user's tag filters may cause an error
      to be returned instead of a submission object. If specified as any
      non-empty string, tag filters will be ignored.

   :query increment_views: If omitted, the view count will not be incremented
      for the specified submission. If specified as any non-empty string while
      :ref:`authenticated <authentication>`, the view count may be increased.

   The result will be a JSON :ref:`submission object <submissions>`.

.. http:get:: /api/journals/(journalid)/view

   View a particular journal by its ``journalid``.

   :query anyway: If omitted, the current user's tag filters may cause an error
      to be returned instead of a journal object. If specified as any non-empty
      string, tag filters will be ignored.

   :query increment_views: If omitted, the view count will not be incremented
      for the specific journal. If specified as any non-empty string while
      :ref:`authenticated <authentication>`, the view count may be increased.

   The result will be a JSON :ref:`journal object <journals>`.

.. http:get:: /api/characters/(charid)/view

   View a particular journal by its ``charid``.

   :query anyway: If omitted, the current user's tag filters may cause an error
      to be returned instead of a character object. If specified as any non-empty
      string, tag filters will be ignored.

   :query increment_views: If omitted, the view count will not be incremented
      for the specific character. If specified as any non-empty string while
      :ref:`authenticated <authentication>`, the view count may be increased.

   The result will be a JSON :ref:`character object <characters>`.


.. http:get:: /api/users/(login_name)/view

   Retrieve information about a user by :term:`login name`.

   The result will be a JSON :ref:`user object <users>`.


.. http:get:: /api/users/(login_name)/gallery

   List a user's gallery by :term:`login name`.

   :query since: An :term:`ISO 8601 timestamp`. If specified, only submissions
      posted after this time will be returned.

   :query count: If specified, no more than this many submissions will be
      returned.

   :query folderid: If specified, only return submissions from the specified
      ``folderid``.

   :query backid: If specified, only return submissions with a ``submitid``
      greater than the ``backid``. This is used in pagination.

   :query nextid: If specified, only return submissions with a ``submitid``
      less than the ``nextid``. This is used in pagination.

   This will return at most 100 submissions. If *count* is more than 100, at
   most 100 submissions will be returned.

   The result will be a JSON object with three keys: *submissions*, *backid*,
   and *nextid*. *submissions* will be a JSON array of :ref:`submission objects
   <submissions>`. *backid* and *nexid* are used in :ref:`pagination
   <pagination>`.


.. http:get:: /api/messages/submissions

   List submissions in an :ref:`authenticated <authentication>` user's inbox.

   :query count: If specified, no more than this many submissions will be
      returned.

   :query backtime: If specified, only return submissions with a ``unixtime``
      greater than the ``backtime``. This is used in pagination.

   :query nexttime: If specified, only return submissions with a ``unixtime``
      less than the ``nexttime``. This is used in pagination.

   This will return at most 100 submissions. If *count* is more than 100, at
   most 100 submissions will be returned.

   The result will be a JSON object with three keys: *submissions*, *backtime*,
   and *nexttime*. *submissions* will be a JSON array of :ref:`submission
   objects <submissions>`. *backtime* and *nextime* are used in
   :ref:`pagination <pagination>`.


.. http:get:: /api/messages/summary

   List a summary of notifications for an :ref:`authenticated <authentication>`
   user. The result will be a JSON object resembling::

     {
         "comments": 0,
         "journals": 3,
         "notifications": 1,
         "submissions": 14,
         "unread_notes": 0
     }

   .. note::

      The result of this API endpoint is cached. New information is available
      only every three minutes or when a note arrives.


.. _submissions:

Submissions
-----------

A basic submission object resembles::

  {
      "media": {},
      "owner": "Fiz",
      "owner_login": "fiz",
      "posted_at": "2012-04-20T00:38:04+00:00Z",
      "rating": "general",
      "submitid": 2031,
      "subtype": "visual",
      "tags": [
           "hunter",
           "snake",
           "pi"
       ],
      "title": "A Wesley!",
      "type": "submission"
  }

The *type* key will be ``"submission"``.

The *subtype* key for ``"submission"`` types will be one of ``"visual"``,
``"literary"``, or ``"multimedia"``.

The *rating* key will be one of ``"general"``, ``"mature"``, or ``"explicit"``.

The *media* key is the submission's :ref:`media <media>`.

Slightly different keys are returned for the
:http:get:`/api/submissions/(submitid)/view` endpoint::

  {
      "comments": 0,
      "description": "<p>(flex)</p>",
      "embedlink": null,
      "favorited": false,
      "favorites": 0,
      "folder_name": "Wesley Stuff",
      "folderid": 2081,
      "friends_only": false,
      "link": "https://www.weasyl.com/submission/2031/a-wesley",
      "media": {
         "submission": [
            {
               "mediaid": 1009285,
               "url": "https://www.weasyl.com/~fiz/submissions/2031/41ebc1c2940be928532785dfbf35c37622664d2fbb8114c3b063df969562fc51/fiz-a-wesley.png"
            }
         ]
      },
      "owner": "Fiz",
      "owner_login": "fiz",
      "owner_media": {
         "avatar": [
            {
               "mediaid": 2610777,
               "url": "https://www.weasyl.com/static/media/8f/38/0f/8f380fc9acb762d7122cb396bb40789ec17bf898bbe832a761d6cc4b497d6e6c.png"
            }
         ]
      },
      "posted_at": "2012-04-20T00:38:04+00:00Z",
      "rating": "general",
      "submitid": 2031,
      "subtype": "visual",
      "tags": [
         "anthro"
      ],
      "title": "A Wesley!",
      "type": "submission",
      "views": 294
  }

The *media* key is the :ref:`media <media>` for the submission itself,
while the *owner_media* key is the :ref:`media <media>` for the owner of the
submission.

The *embedlink* key will be ``null`` for ``"visual"`` type submissions and
potentially a URL for other submission types.

The *description* key is the HTML-rendered description of the submission.

The *favorited* key indicates whether or not the current user has favorited
the submission.


.. _journals:

Journals
--------

A basic journal object resembles::

   {
       "comments": 3,
       "content": "<p>Man, I can't believe this site's been in development for a whole year! I'm so excited that everyone finally gets to use it, including myself! What do you all think so far?</p>",
       "favorited": false,
       "favorites": 0,
       "friends_only": false,
       "journalid": 2028,
       "link": "https://www.weasyl.com/journal/2028/wow-this-is-amazing",
       "owner": "Wesley",
       "owner_login": "wesley",
       "owner_media": {
           "avatar": [
               {
                   "mediaid": 934000,
                   "url": "https://cdn.weasyl.com/static/media/b0/46/a3/b046a3f7a5b6aa936f393f68ccef68d85afe4aeed43af415b81c41739701edde.gif"
               }
           ]
       },
       "posted_at": "2012-09-30T08:23:12Z",
       "rating": "general",
       "tags": [
           "happy",
           "introduction",
           "weasyl"
       ],
       "title": "Wow, this is amazing!",
       "type": "journal",
       "views": 174
   }

The *title* is the journal's title.

The *content* is the journal's content.


.. _characters:

Characters
----------

A basic character object resembles::

   {
      "age": "young",
      "charid": 63670,
      "comments": 0,
      "content": "<p>Hi! I'm just creating a little character profile for myself. We all want those, right?</p>",
      "favorited": false,
      "favorites": 0,
      "friends_only": false,
      "gender": "",
      "height": "",
      "link": "https://www.weasyl.com/character/63670/wesley",
      "media": {
         "submission": [
            {
               "mediaid": null,
               "url": "https://cdn.weasyl.com/static/character/94/4d/a7/e0/a0/7a/wesley-63670.submit.2000.png"
            }
         ]
      },
      "owner": "Wesley",
      "owner_login": "wesley",
      "owner_media": {
          "avatar": [
              {
                  "mediaid": 5223401,
                  "url": "https://cdn.weasyl.com/static/media/b0/46/a3/b046a3f7a5b6aa936f393f68ccef68d85afe4aeed43af415b81c41739701edde.gif"
              }
          ]
      },
      "posted_at": "2016-06-02T18:07:54Z",
      "rating": "general",
      "species": "weasel",
      "tags": [
          "weasel"
      ],
      "title": "Wesley",
      "type": "character",
      "views": 1,
      "weight": ""
   }

The *title* is the character's name.

The *content* is the character's description.

The *age*, *gender*, *height*, *species*, and *weight* keys are information about the character.


.. _users:

Users
-----

A user object contains many keys. Some of these keys include:

   ``media``
      The :ref:`media <media>` of the specified user's avatar and banner.

   ``profile_text``
      The rendered HTML of the specified user's description.

   ``recent_submissions``
      An array of :ref:`submission objects <submissions>`.

   ``recent_type``
      What kind of submissions are in the ``recent_submissions`` array. Can
      be one of ``submissions``, ``characters``, or ``collections``.

   ``relationship``
      ``null`` if this is an unauthenticated request or an object
      representing aspects of the relationship between the current user and
      the specified user.

   ``show_favorites_bar``
      Whether the specified user's favorites are shown as icons at the top
      of the profile page.

   ``show_favorites_tab``
      Whether the specified user's favorites should be shown at all.

   ``statistics``
      ``null`` if the specified user doesn't allow statistics to be shown or
      an object of statistics about the specified user.


A user object resembles::

  {
      "banned": false,
      "catchphrase": "",
      "commission_info": {
          "commissions": null,
          "details": "&lt;",
          "price_classes": null,
          "requests": null,
          "trades": null
      },
      "created_at": "2012-11-03T17:01:37Z",
      "featured_submission": null,
      "folders": [],
      "full_name": "weyk\u00ebnt",
      "login_name": "weykent",
      "media": {
          "avatar": [
              {
                  "mediaid": 937444,
                  "url": "https://www.weasyl.com/static/user/66/42/8d/0a/3f/8c//5756/avatar.png"
              }
          ],
          "banner": [
              {
                  "mediaid": 937443,
                  "url": "https://www.weasyl.com/static/user/66/42/8d/0a/3f/8c//5756/banner.gif"
              }
          ]
      },
      "profile_text": "<p>yo. I do weasyl coding and shit.</p><p>&#128572;</p>",
      "recent_submissions": [],
      "recent_type": "collections",
      "relationship": null,
      "show_favorites_bar": false,
      "show_favorites_tab": false,
      "statistics": {
          "faves_received": 0,
          "faves_sent": 2,
          "followed": 23,
          "following": 56,
          "journals": 0,
          "page_views": 16354,
          "submissions": 0
      },
      "stream_text": "",
      "stream_url": "",
      "streaming_status": "stopped",
      "suspended": false,
      "user_info": {
          "age": null,
          "aim": "",
          "facebook": "",
          "foursquare": "",
          "gender": "h4x0r",
          "googleplus": "",
          "icq": "",
          "location": "seattle, wa",
          "msn": "",
          "myspace": "",
          "psn": "",
          "reddit": "",
          "skype": "",
          "steam": "",
          "tumblr": "",
          "twitter": "",
          "xboxlive": "",
          "yahoo": "",
          "youtube": ""
      },
      "username": "weykent"
  }


.. _media:

Media keys
----------

*media* keys in Weasyl API responses take the form of a JSON object mapping
descriptive names to media file objects.

The media file objects will have at least two keys: *url*, and *mediaid*. The
*mediaid* is a unique identifier which unambiguously refers to a particular
file stored by Weasyl. The *url* is one possible URL where the file can be
downloaded. There can be multiple possible *url*\ s for a given *mediaid*. A
*mediaid* can also be ``null`` to indicate the *url* is already unambiguous.

For submissions, the possible descriptive names are ``"submission"`` for the
original file uploaded by the user, ``"cover"`` for the submission's
:term:`cover image`, and ``"thumbnail"`` for the submission's thumbnail. The
``"submission"`` and ``"cover"`` names are optional for a submission, while the
``"thumbnail"`` name will always exist.

For users, the possible descriptive names are ``"avatar"`` for the user's
avatar and ``"banner"`` for the user's banner. ``"banner"`` is optional while
``"avatar"`` will always exist.

Here is an example of the media for a visual submission::

  {
    "submission": [
      {
        "mediaid": 1651999,
        "url": "https://www.weasyl.com/static/media/..."
      }
    ],
    "thumbnail": [
      {
        "mediaid": 1652001,
        "url": "https://www.weasyl.com/static/media/..."
      }
    ],
    "cover": [
      {
        "mediaid": 1651999,
        "url": "https://www.weasyl.com/static/media/..."
      }
    ]
  }


.. _pagination:

Pagination
----------

Pagination is done through *backid* and *nextid* (or, in some cases, *backtime*
and *nexttime*) response keys and request query parameters. Paginated API
endpoints will return JSON objects with *backid* and *nextid* keys to indicate
how to find the previous and next pages of results.

If *nextid* is not ``null``, there is a next page accessible by specifying that
*nextid* as a query parameter, keeping all other query parameters the same.
Similarly, if *backid* is not ``null``, there is a previous page accessible by
specifying that *backid* as a query parameter.


.. _authentication:

Authentication
--------------

Authentication can be done with a Weasyl API key.

Weasyl API keys are managed at <https://www.weasyl.com/control/apikeys>, and
are extremely simple to use. To authenticate a request, set the
``X-Weasyl-API-Key`` header to the value of an API key, and the user agent will
be authenticated as the user who created the key.


Errors
------

At the moment, these are the non-:http:statuscode:`200` statuses potentially
emitted by the Weasyl API:

- :http:statuscode:`401`. This is emitted for resources which require an
  :ref:`authenticated <authentication>` user if no authorization is provided,
  or if the provided authorization is invalid.

- :http:statuscode:`403`. This is emitted in the case of an expected error.
  That is, Weasyl was able to process your request, but is unable to return the
  requested entity for some reason.

- :http:statuscode:`404`. This is emitted if a URL is requested which doesn't
  have matching data. For example, a request to
  :http:get:`/api/users/(login_name)/gallery` for a :term:`login name` which
  doesn't exist.

- :http:statuscode:`422`. This is emitted if a parameter's value is unparsable
  or invalid. For example, if a non-numeric value is specified for a parameter
  requiring a numeric value.

- :http:statuscode:`500`. This is emitted in the case of an unexpected error.
  That is, Weasyl was unable to process your request.

In addition to sending a non-:http:statuscode:`200` response, errors are
signaled by returning a JSON object with an *error* key. The value of this key
will be an object containing either a *code* key, a *name* key, or neither. An
object with a *code* or *name* key will unambiguously specify the problem
encountered. An object with neither key indicates that an unexpected error was
encountered.

An error response resembles the following::

    {
      "error": {
        "name": "RatingExceeded"
      }
    }


Glossary
========

.. glossary::

   cover image

      The image displayed on the submission page, which may be smaller than the
      actual submission file. Cover images will be no larger than 1024 pixels
      by 3000 pixels.


   ISO 8601 timestamp

      A string representing a particular moment in time. Weasyl requires
      exactly one of the formats described by ISO 8601:
      ``YYYY-MM-DDTHH:MM:SSZ``. For example, ``2014-02-12T17:00:00Z``. As this
      includes a trailing ``Z``, the time is required to be in UTC.


   login name

      A user's username, lowercase, and omitting all non-alphanumeric,
      non-ASCII characters.
