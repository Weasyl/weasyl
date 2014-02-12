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

   If there is no current user, the result will be::

     {"login": null, "userid": 0}


.. http:get:: /api/useravatar

   A user's avatar.

   :query username: The user's :term:`login name`.

   The result will resemble::

     {"avatar": "https://www.weasyl.com/static/user/66/42/8d/0a/3f/8c/5756/avatar.png"}

   Users without an avatar will get the default avatar icon back.


.. http:get:: /api/submissions/frontpage

   A list of submissions from the front page, respecting the current user's
   browsing settings.

   :query since: A UNIX epoch time. Only submissions posted after this time
      will be returned.

   :query count: No more than this many submissions will be returned.

   This will return at most 100 submissions. If *count* is more than 100, at
   most 100 submissions will be returned. It is possible to receive less than
   *count* submissions back if too many submissions are filtered by the user's
   e.g. tag filters.

   The result will be a JSON array of :ref:`submissions <submissions>`.


.. http:get:: /api/submissions/(submitid)/view

   View a particular submission by its ``submitid``.

   :query anyway: If omitted, the current user's tag filters may cause an error
      to be returned instead of a submission object. If specified as any
      non-empty string, tag filters will be ignored.

   :query increment_views: If omitted, the view count will not be incremented
      for the specified submission. If specified as any non-empty string while
      authenticated, the view count may be increased.

   The result will be a :ref:`submission object <submissions>`.


.. _submissions:

Submissions
-----------

   A basic submission object resembles::

     {
       "type": "submission",
       "subtype": "visual",
       "rating": "general",
       "tags": [
         "hunter",
         "snake",
         "pi"
       ],
       "owner": "Caffeinated-Owl",
       "owner_login": "caffeinatedowl",
       "submitid": 466821,
       "title": "Tiny Little Pi",
       "media": {...},
       "posted_at": "2014-02-12T07:33:17Z"
     }

   The *type* key will be one of ``"submission"`` or ``"character"``.

   The *subtype* key for ``"submission"`` types will be one of ``"visual"``,
   ``"literary"``, or ``"multimedia"``.

   The *rating* key will be one of ``"general"``, ``"moderate"``, ``"mature"``,
   or ``"explicit"``.

   The *media* key is explained in the :ref:`media section <media>`.

   Slightly different keys are returned for the
   :http:get:`/api/submissions/(submitid)/view` endpoint::

     {
         "comments": 0,
         "description": "Itty bitty little snake hunter",
         "embedlink": null,
         "favorited": false,
         "favorites": 3,
         "folder_name": null,
         "folderid": null,
         "friends_only": false,
         "owner": "Caffeinated-Owl",
         "owner_login": "caffeinatedowl",
         "owner_media": {...},
         "posted_at": "2014-02-12T07:33:17Z",
         "rating": "general",
         "sub_media": {...},
         "submitid": 466821,
         "subtype": "visual",
         "tags": [
             "hunter",
             "pi",
             "snake"
         ],
         "title": "Tiny Little Pi",
         "type": "submission",
         "views": 6
     }

   The *sub_media* key is the media for the submission itself, while the
   *owner_media* key is the media for the owner of the submission.

   The *embedlink* key will be ``null`` for ``"visual"`` type submissions and
   potentially a URL for other submission types.

   The *description* key is the Markdown-formatted description of the
   submission.

   The *favorited* key indicates whether or not the current user has favorited
   the submission.


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

A media file object may also have another key: *links*. The *links* key is
itself a media key, and allows media files to be linked to other media files.
Currently, the only kind of link is ``"cover"``, which links a media file to
its :term:`cover image`.

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
        "links": {
          "cover": [
            {
              "mediaid": 1651999,
              "url": "https://www.weasyl.com/static/media/..."
            }
          ]
        },
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
        "links": {
          "cover": [
            {
              "mediaid": 1651999,
              "url": "https://www.weasyl.com/static/media/..."
            }
          ]
        },
        "mediaid": 1651999,
        "url": "https://www.weasyl.com/static/media/..."
      }
    ]
  }


Glossary
========

.. glossary::

   cover image

      The image displayed on the submission page, which may be smaller than the
      actual submission file. Cover images will be no larger than 1024 pixels
      by 3000 pixels.


   login name

      A user's username, omitting all non-alphanumeric, non-ASCII characters.
