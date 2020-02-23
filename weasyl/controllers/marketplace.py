from __future__ import absolute_import

from pyramid.view import view_config

from weasyl import define, media, commishinfo


@view_config(route_name="marketplace", renderer='/etc/marketplace.jinja2')
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
    return {
        'results': results,
        'form': form,
        'currencies': commishinfo.CURRENCY_CHARMAP,
        'presets': commishinfo.PRESET_COMMISSION_CLASSES,
        'previndex': prev_index,
        'nextindex': next_index
    }
