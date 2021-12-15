"""DataBase models."""
from sqlalchemy import Column, ForeignKey, Integer, Text, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    """Product."""

    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)

    name = Column(Text, unique=True)
    is_bundle = Column(Boolean)

    items = relationship('ProductItem', back_populates='product')

    creator_id = Column(Integer, ForeignKey('creators.id'))
    creator = relationship('Creator', back_populates='products')


class ProductItem(Base):
    """Product item in market palce."""

    __tablename__ = 'product_item'

    id = Column(Integer, primary_key=True)

    name = Column(Text)
    url = Column(Text, unique=True)

    personal_price_cents = Column(Integer)
    commercial_price_cents = Column(Integer)
    extended_price_cents = Column(Integer)
    special_license = Column(Text)
    category = Column(Text)
    is_live = Column(Boolean)

    product_id = Column(Integer, ForeignKey('products.id'))
    product = relationship('Product', back_populates='items')

    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship('Account', back_populates='product_items')

    sales = relationship('Sale', back_populates='product_item')


class Sale(Base):
    """Sale."""

    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True)

    date = Column(Date)
    price_cents = Column(Integer)
    earning_cents = Column(Integer)

    product_item_id = Column(Integer, ForeignKey('product_item.id'))
    product_item = relationship('ProductItem', back_populates='sales')


class MarketPlace(Base):
    """Market place."""

    __tablename__ = 'market_places'

    id = Column(Integer, primary_key=True)

    domain = Column(Text, unique=True)
    name = Column(Text)

    accounts = relationship('Account', back_populates='market_place')


class Account(Base):
    """Account."""

    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)

    username = Column(Text)

    market_place_id = Column(Integer, ForeignKey('market_places.id'))
    market_place = relationship('MarketPlace', back_populates='accounts')

    cookies = relationship('Cookie', back_populates='account')

    product_items = relationship('ProductItem', back_populates='account')


class Creator(Base):
    """Creator."""

    __tablename__ = 'creators'

    id = Column(Integer, primary_key=True)

    name = Column(Text)

    products = relationship('Product', back_populates='creator')


class Cookie(Base):
    """Cookie."""

    __tablename__ = 'cookies'

    id = Column(Integer, primary_key=True)

    data = Column(Text)

    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship('Account', back_populates='cookies')
