import json
import os

from pb_design_parsers import db, models
from cryptography.fernet import Fernet
from datetime import datetime


def get_cookies(domain: str, username: str) -> list[dict]:
    domain_cookies: list = []
    with db.SessionLocal() as session:
        market_place = session.query(models.MarketPlace).filter_by(domain=domain).first()
        if not market_place:
            return domain_cookies

        account = session.query(models.Account).filter_by(
            username=username,
            market_place=market_place,
        ).first()
        if not account:
            return domain_cookies

        key = os.environ.get('KEY') or 'secret'
        fernet = Fernet(key.encode('UTF-8'))

        cookies = session.query(models.Cookie).filter_by(
            account=account,
        ).all()
        for cookie in cookies:
            domain_cookies.append(
                json.loads(fernet.decrypt(cookie.data).decode())
            )
    return domain_cookies


def set_cookies(domain: str, username: str, cookies: list):
    with db.SessionLocal() as session:
        delete_cookies(domain, username)

        key = os.environ.get('KEY') or 'secret'
        fernet = Fernet(key.encode('UTF-8'))

        market_place = session.query(models.MarketPlace).filter_by(domain=domain).first()
        if not market_place:
            market_place = models.MarketPlace(domain=domain)
            session.add(market_place)

        account = session.query(models.Account).filter_by(
            username=username,
            market_place=market_place,
        ).first()
        if not account:
            account = models.Account(username=username, market_place=market_place)
            session.add(account)

        for cookie in cookies:
            session.add(models.Cookie(
                account=account,
                data=fernet.encrypt(json.dumps(cookie).encode('UTF-8')),
            ))
        session.commit()


def delete_cookies(domain: str, username: str):
    with db.SessionLocal() as session:
        market_place = session.query(models.MarketPlace).filter_by(domain=domain).first()
        if not market_place:
            return

        account = session.query(models.Account).filter_by(
            username=username,
            market_place=market_place,
        ).first()
        if not account:
            return
        current_cookies = session.query(models.Cookie).filter_by(
            account=account,
        ).all()

        for cookie in current_cookies:
            session.delete(cookie)
            session.commit()


def add_sale(
    date: datetime,
    price: int,
    earnings: int,
    product: str,
    reffered: bool,
    market_place_domain: str,
):
    with db.SessionLocal() as session:
        market_place = session.query(models.MarketPlace).filter_by(
            domain=market_place_domain
        ).first()
        if not market_place:
            market_place = models.MarketPlace(domain=market_place_domain)
            session.add(market_place)

        db_product = session.query(models.Product).filter_by(name=product).first()
        if not db_product:
            db_product = models.Product(
                name=product,
                own=not reffered,
            )
            session.add(db_product)
        elif db_product.own is False and reffered is False:
            db_product.own = True

        sale = models.Sale(
            date=date,
            price_cents=price,
            earning_cents=earnings,
            product=db_product,
            market_place=market_place,
        )
        session.add(sale)

        session.commit()
