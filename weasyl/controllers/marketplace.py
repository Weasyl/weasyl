import dataclasses
from dataclasses import dataclass

from pyramid.response import Response

from weasyl import define, media, commishinfo


@dataclass(frozen=True, kw_only=True, slots=True)
class SearchForm:
    pc: str
    c: str
    q: str
    min: str
    max: str
    currency: str

    @classmethod
    def from_get(cls, params):
        return cls(
            pc=params.get("pc", ""),
            c=params.get("c", ""),
            q=params.get("q", ""),
            min=params.get("min", ""),
            max=params.get("max", ""),
            currency=params.get("currency", ""),
        )

    asdict = dataclasses.asdict


def search_(request):
    limit = 30
    offset = define.get_int(request.GET.get('o'))
    form = SearchForm.from_get(request.GET)
    commishclass = form.pc if form.pc else form.c
    commishclass = commishclass.lower()

    results = commishinfo.select_commissionable(userid=request.userid,
                                                q=form.q,
                                                commishclass=commishclass,
                                                min_price=commishinfo.parse_currency(form.min),
                                                max_price=commishinfo.parse_currency(form.max),
                                                currency=form.currency,
                                                offset=offset,
                                                limit=limit * 2)
    rcount = len(results)
    results = results[0:limit]
    media.populate_with_user_media(results)
    prev_index = None if offset == 0 else offset - limit if offset - limit > 0 else 0
    next_index = offset + limit if rcount - limit > 0 else None
    return Response(define.webpage(request.userid, "etc/marketplace.html",
                    [results, form, commishinfo.CURRENCY_CHARMAP, commishinfo.PRESET_COMMISSION_CLASSES,
                     prev_index, next_index],
                    title='Marketplace'))
