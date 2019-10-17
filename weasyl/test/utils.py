


class Bag(object):
    def __init__(self, **kw):
        for kv in list(kw.items()):
            setattr(self, *kv)
