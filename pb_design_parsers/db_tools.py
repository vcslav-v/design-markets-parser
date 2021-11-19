import json
import os

from pb_design_parsers import db, models
from pb_design_parsers import REFER_PRODUCT_NAME
from cryptography.fernet import Fernet
from datetime import datetime
from loguru import logger


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
                json.loads(fernet.decrypt(cookie.data.encode('UTF-8')).decode('UTF-8'))
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
            account = models.Account(username=username, market_place=market_place)
            session.add(account)
            session.add(market_place)
        else:
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
                data=fernet.encrypt(json.dumps(cookie).encode('UTF-8')).decode('utf-8'),
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
    date: datetime = None,
    price: int = None,
    earnings: int = None,
    product: str = None,
    reffered: bool = False,
    market_place_domain: str = None,
    username: str = None,
):
    product_name = product if not reffered else REFER_PRODUCT_NAME
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
            session.commit()
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
                session.commit()

        db_product_item = session.query(models.ProductItem).filter_by(
            name=product_name,
            account=account,
        ).first()

        if not db_product_item:
            db_product = session.query(models.Product).filter_by(name=product_name).first()
            if not db_product:
                db_product = models.Product(name=product_name)
                session.add(db_product)
            db_product_item = models.ProductItem(
                name=product_name,
                account=account,
                product=db_product,
            )
            session.add(db_product_item)

        sale = models.Sale(
            date=date,
            price_cents=price,
            earning_cents=earnings,
            product_item=db_product_item,
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

        sql_request = f"""
        select date
        from sales join product_item on sales.product_item_id = product_item.id
        where product_item.account_id = {account.id}
        order by sales.date desc
        limit 1;
        """
        db_response = session.execute(sql_request)
        for row in db_response:
            return row[0].date()
        return datetime.fromtimestamp(0).date()


def add_product_item(
    market_domain: str,
    account_name: str,
    name: str,
    url: str,
    is_live: bool,
    categories: list,
    licenses: dict,
):
    with db.SessionLocal() as session:
        db_market = session.query(models.MarketPlace).filter_by(domain=market_domain).first()
        if not db_market:
            db_market = models.MarketPlace(domain=market_domain)
            session.add(db_market)
            session.commit()

        db_account = session.query(models.Account).filter_by(
            username=account_name,
            market_place=db_market,
        ).first()
        if not db_account:
            db_account = models.Account(
                username=account_name,
                market_place=db_market,
            )
            session.add(db_account)
            session.commit()

        db_product_item = session.query(models.ProductItem).filter_by(
            name=name,
            account=db_account
        ).first()
        if not db_product_item:
            db_product = session.query(models.Product).filter_by(name=name).first()
            if not db_product:
                db_product = models.Product(name=name)
                session.add(db_product)
            db_product_item = models.ProductItem(name=name, account=db_account, product=db_product)

        db_product_item.url = url
        db_product_item.category = '/'.join(categories)
        db_product_item.is_live = is_live

        db_product_item.special_license = None
        for name_license, price in licenses.items():
            if 'personal' in name_license.lower():
                db_product_item.personal_price_cents = price
            elif 'commercial' in name_license.lower() and 'extended' not in name_license.lower():
                db_product_item.commercial_price_cents = price
            elif 'extended' in name_license.lower():
                db_product_item.extended_price_cents = price
            else:
                license_text = f'{name_license}-{price}'.lower()
                if db_product_item.special_license:
                    db_product_item.special_license = '/'.join(
                        [db_product_item.special_license, license_text],
                    )
                else:
                    db_product_item.special_license = license_text

        session.add(db_product_item)
        session.commit()


@logger.catch
def get_all_products_info():
    sql_request = """
        SELECT products.id, products.name, string_agg(product_item.url, '|')
        FROM products JOIN product_item on products.id = product_item.product_id
        WHERE product_item.is_live and product_item.url is not null
        GROUP BY products.id
        ORDER BY products.name;
    """
    with db.SessionLocal() as session:
        db_responce = session.execute(sql_request)
        result = [(*row[:-1], row[-1].split('|')) for row in db_responce]

    return result


@logger.catch
def merge_products(main_product_id, additional_product_id):
    with db.SessionLocal() as session:
        main_product = session.query(models.Product).filter_by(
            id=main_product_id
        ).first()
        additional_product = session.query(models.Product).filter_by(
            id=additional_product_id
        ).first()

        for additional_product_item in additional_product.items:
            main_product.items.append(additional_product_item)

        session.delete(additional_product)
        session.commit()
