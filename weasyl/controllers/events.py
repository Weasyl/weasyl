from weasyl import define
from weasyl.controllers.decorators import controller_base


class halloweasyl2014_(controller_base):
    def GET(self):
        return define.webpage(userid=self.user_id, template='events/halloweasyl.html')
