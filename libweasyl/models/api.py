from sqlalchemy.orm import relationship

from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables


class APIToken(Base):
    __table__ = tables.api_tokens

    user = relationship(Login, backref='api_keys')
