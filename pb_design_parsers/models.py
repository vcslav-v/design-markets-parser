"""DataBase models."""
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Cookie(Base):
    """Cookie."""

    __tablename__ = 'cookies'

    id = Column(Integer, primary_key=True)

    domain = Column(Text)
    username = Column(Text)
    data = Column(Text)
