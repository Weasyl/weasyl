from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query

from libweasyl.models.tables import metadata


class BaseQuery(Query):
    # set by configure_libweasyl
    _not_found_exception = None

    def get_or_404(self, ident):
        ret = self.get(ident)
        if ret is None:
            raise self._not_found_exception()
        return ret


registry = {}
Base = declarative_base(
    class_registry=registry, metadata=metadata)


def _configure_dbsession(dbsession):
    """
    Called by configure_libweasyl to specify the globally-used SQLAlchemy
    session object.
    """
    Base.dbsession = dbsession
    Base.query = dbsession.query_property(BaseQuery)
