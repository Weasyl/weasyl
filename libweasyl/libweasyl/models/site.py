from sqlalchemy.orm import relationship

from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables


class SiteUpdate(Base):
    __table__ = tables.siteupdate

    owner = relationship(Login, backref='siteupdate')

    def canonical_path(self, request, operation='view'):
        parts = ['site-updates', str(self.updateid)]

        if operation in ('delete', 'edit'):
            parts.append(operation)

        return request.resource_path(None, *parts)


class SavedNotification(Base):
    __table__ = tables.welcome

    owner = relationship(Login, backref='saved_notifications')
