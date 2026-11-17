from sqlalchemy.ext.declarative import declarative_base

from libweasyl.models.tables import metadata


registry = {}
Base = declarative_base(
    class_registry=registry, metadata=metadata)


def _configure_dbsession(dbsession):
    """
    Called by configure_libweasyl to specify the globally-used SQLAlchemy
    session object.
    """
    Base.dbsession = dbsession
    Base.query = dbsession.query_property()
