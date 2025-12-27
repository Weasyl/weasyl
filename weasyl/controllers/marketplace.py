from pyramid.response import Response

from weasyl import define, media, commishinfo


def search_(request):
    form = request.web_input(q="", min="", max="", currency="", pc="", c="", o="")
    limit = 30
    offset = define.get_int(form.o)
    commishclass = form.pc if form.pc else form.c
    commishclass = commishclass.lower()

    results = commishinfo.select_commissionable(request.userid,
                                                form.q,
                                                commishclass,
                                                commishinfo.parse_currency(form.min),
                                                commishinfo.parse_currency(form.max),
                                                form.currency,
                                                offset,
                                                limit * 2,)
    rcount = len(results)
    results = results[0:limit]
    media.populate_with_user_media(results)
    prev_index = None if offset == 0 else offset - limit if offset - limit > 0 else 0
    next_index = offset + limit if rcount - limit > 0 else None
    return Response(define.webpage(request.userid, "etc/marketplace.html",
                    [results, form, commishinfo.CURRENCY_CHARMAP, commishinfo.PRESET_COMMISSION_CLASSES,
                     prev_index, next_index],
                    title='Marketplace'))
