from __future__ import absolute_import

from pyramid.response import Response

from weasyl import define, media, commishinfo


def search_(request):
    limit = 30
    offset = define.get_int(request.params.get('o', None))
    pc = request.params.get('pc', '')
    c = request.params.get('c', '')
    commishclass = pc if pc else c
    commishclass = commishclass.lower()
    q = request.params.get('q', '')
    min_value = request.params.get('min', '')
    max_value = request.params.get('max', '')
    currency = request.params.get('currency', '')

    results = commishinfo.select_commissionable(request.userid,
                                                q,
                                                commishclass,
                                                commishinfo.parse_currency(min_value),
                                                commishinfo.parse_currency(max_value),
                                                currency,
                                                offset,
                                                limit * 2,)
    rcount = len(results)
    results = results[0:limit]
    media.populate_with_user_media(results)
    prev_index = None if offset == 0 else offset - limit if offset - limit > 0 else 0
    next_index = offset + limit if rcount - limit > 0 else None
    form = {'pc': pc, 'c': c, 'q': q, 'min': min_value, 'max': max_value, 'currency': currency}
    return Response(define.webpage(request.userid, "etc/marketplace.html",
                    [results, form, commishinfo.CURRENCY_CHARMAP, commishinfo.PRESET_COMMISSION_CLASSES,
                     prev_index, next_index]))
