import json

from pyramid.response import Response

from libweasyl.exceptions import WeasylError
from weasyl import define, profile


def webfinger(request):
    """Handle WebFinger requests."""
    resource = request.params.get('resource')
    if not resource or not resource.startswith('acct:'):
        raise WeasylError("Invalid resource parameter")

    if resource.count("@")>2:
        username = resource.split('@')[1].replace('acct:', '')
    else:
        username = resource.split('@')[0].replace('acct:', '')
    define.append_to_log("well_known.webfinger", username=username)
    username = request.matchdict.get('name', username)
    userid = define.get_int(request.params.get('userid'))
    url = define.absolutify_url("")
    domain = url.replace("http://","").replace("https://","")
    user = profile.resolve(request.userid, userid, username)
    if not user:
        raise WeasylError("User not found")

    response = {
        "subject": f"acct:{username}@{domain}",
        "links": [
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": f"{url}/user/{username}"
            }
        ]
    }

    return Response(json.dumps(response), content_type="application/json", charset="utf-8")