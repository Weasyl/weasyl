from __future__ import absolute_import


class Bag(object):
    def __init__(self, **kw):
        for kv in kw.items():
            setattr(self, *kv)
