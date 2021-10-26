import json
import os

from pb_design_parsers import db, models
from pb_design_parsers import REFER_PRODUCT_NAME
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
    username: str
):
    with db.SessionLocal() as session:
        market_place = session.query(models.MarketPlace).filter_by(
            domain=market_place_domain
        ).first()
        if not market_place:
            market_place = models.MarketPlace(domain=market_place_domain)
            account = models.Account(
                username=username,
                market_place=market_place,
            )
            session.add(account)
            session.add(market_place)
        else:
            account = session.query(models.Account).filter_by(
                username=username,
                market_place=market_place,
            ).first()
            if not account:
                account = models.Account(
                    username=username,
                    market_place=market_place,
                )
                session.add(account)
        if reffered:
            db_product = session.query(models.Product).filter_by(name=REFER_PRODUCT_NAME).first()
        else:
            db_product = session.query(models.Product).filter_by(name=product).first()

        if not db_product:
            db_product = models.Product(
                name=product if not reffered else REFER_PRODUCT_NAME,
            )
            session.add(db_product)

        
            

        sale = models.Sale(
            date=date,
            price_cents=price,
            earning_cents=earnings,
            product=db_product,
            market_place=market_place,
            account=account,
        )

        session.add(sale)
        session.commit()


def get_last_date_in_db(domain, username):
    with db.SessionLocal() as session:

        market_place = session.query(models.MarketPlace).filter_by(domain=domain).first()
        if not market_place:
            return datetime.fromtimestamp(0).date()

        account = session.query(models.Account).filter_by(
            username=username, market_place=market_place
        ).first()
        if not account:
            return datetime.fromtimestamp(0).date()

        sale = session.query(models.Sale).filter_by(
            market_place=market_place,
            account=account,
        ).order_by(models.Sale.date.desc()).first()
        if sale:
            return sale.date
        else:
            return datetime.fromtimestamp(0).date()
