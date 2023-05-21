from sqlalchemy.orm import relationship

from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables


class SavedNotification(Base):
    __table__ = tables.welcome

    owner = relationship(Login, backref='saved_notifications')
