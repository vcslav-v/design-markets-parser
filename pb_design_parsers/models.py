"""DataBase models."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, LargeBinary, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    """Product."""

    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)

    name = Column(Text, unique=True)
    own = Column(Boolean)

    sales = relationship('Sale', back_populates='product')


class Sale(Base):
    """Sale."""

    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    price_cents = Column(Integer)
    earning_cents = Column(Integer)

    product_id = Column(Integer, ForeignKey('products.id'))
    product = relationship('Product', back_populates='sales')

    market_place_id = Column(Integer, ForeignKey('market_places.id'))
    market_place = relationship('MarketPlace', back_populates='sales')


class MarketPlace(Base):
    """Market place."""

    __tablename__ = 'market_places'

    id = Column(Integer, primary_key=True)

    domain = Column(Text, unique=True)

    accounts = relationship('Account', back_populates='market_place')
    sales = relationship('Sale', back_populates='market_place')


class Account(Base):
    """Account."""

    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)

    username = Column(Text)

    market_place_id = Column(Integer, ForeignKey('market_places.id'))
    market_place = relationship('MarketPlace', back_populates='accounts')

    cookies = relationship('Cookie', back_populates='account')


class Cookie(Base):
    """Cookie."""

    __tablename__ = 'cookies'

    id = Column(Integer, primary_key=True)

    data = Column(LargeBinary)

    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship('Account', back_populates='cookies')
