from sqlalchemy.orm import relationship

from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables


class SiteUpdate(Base):
    __table__ = tables.siteupdate

    owner = relationship(Login, backref='siteupdate')


class SavedNotification(Base):
    __table__ = tables.welcome

    owner = relationship(Login, backref='saved_notifications')
