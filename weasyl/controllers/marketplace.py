from pyramid.response import Response

from weasyl import define, media, commishinfo


def search_(request):
    form = request.web_input(q="", min="", max="", currency="", pc="", c="")
    commishclass = form.c if form.c else form.pc
    commishclass = commishclass.lower()

    results = commishinfo.select_commissionable(request.userid,
                                                form.q,
                                                commishclass,
                                                commishinfo.parse_currency(form.min),
                                                commishinfo.parse_currency(form.max),
                                                form.currency,
                                                30,)

    media.populate_with_user_media(results)
    return Response(define.webpage(request.userid, "etc/marketplace.html",
                          [results, form, commishinfo.CURRENCY_CHARMAP, commishinfo.PRESET_COMMISSION_CLASSES]))
