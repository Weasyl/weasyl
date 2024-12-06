import json

from pyramid.response import Response

from libweasyl.exceptions import WeasylError
from weasyl import define, profile


def webfinger(request):
    """Handle WebFinger requests."""
    resource = request.params.get('resource')
    if not resource or not resource.startswith('acct:'):
        raise WeasylError("Invalid resource parameter")

    if resource.count("@") > 2 or resource.count("@") < 1:
        raise WeasylError("Invalid resource parameter")
    elif resource.count("@") == 2:
        username = resource.split('@')[1].replace('acct:', '')
    else:
        username = resource.split('@')[0].replace('acct:', '')
    define.append_to_log("well_known.webfinger", username=username)
    username = request.matchdict.get('name', username)
    userid = define.get_int(request.params.get('userid'))
    url = define.absolutify_url("")
    domain = url.replace("http://", "").replace("https://", "")
    user = profile.resolve(request.userid, userid, username)
    userprofile = profile.select_profile(user, viewer=request.userid)
    avatar_url = define.absolutify_url(userprofile['user_media']['avatar'][0]['display_url'])
    if not user:
        raise WeasylError("User not found")

    response = {
        "subject": f"acct:{username}@{domain}",
        "aliases": [
            f"{url}/user/{username}",
            f"{url}/profile/{username}",
            f"{url}/~{username}"
        ],
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"{url}/user/{username}"
            },
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": f"{url}/~{username}"
            },
            # unsupported, but would be cool?
            # {
            #     "rel": "http://schemas.google.com/g/2010#updates-from",
            #     "type": "application/atom+xml",
            #     "href": f"{url}/user/{username}.atom"
            # },
            {
                "rel": "http://webfinger.net/rel/avatar",
                "type": "image/png",
                "href": f"{avatar_url}"
            }
        ]
    }

    return Response(json.dumps(response), content_type="application/json", charset="utf-8")
