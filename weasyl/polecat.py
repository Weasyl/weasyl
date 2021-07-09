"""Polecats are twisted weasyls.

Just bear with me here.
"""

from twisted.web.server import Site


class WeasylSite(Site):
    def log(self, request):
        "Do nothing; we don't need request logging."
