from sqlalchemy.orm import relationship

from libweasyl.models.meta import Base
from libweasyl.models.users import Login
from libweasyl.models import tables


class APIToken(Base):
    __table__ = tables.api_tokens

    user = relationship(Login, backref='api_keys')


class OAuthConsumer(Base):
    __table__ = tables.oauth_consumers

    owner = relationship(Login, backref='oauth_consumers')

    @property
    def client_id(self):
        return self.clientid


class OAuthBearerToken(Base):
    __table__ = tables.oauth_bearer_tokens

    user = relationship(Login, backref='bearer_tokens')
