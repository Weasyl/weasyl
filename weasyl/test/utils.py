from __future__ import absolute_import


class Bag(object):
    """
    An object with attributes.

    It takes keyword arguments and sets their values as attributes.
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
