import json

import db
import models


def get_cookies(domain: str, username: str) -> list[dict]:
    domain_cookies = []
    with db.SessionLocal() as session:
        cookies = session.query(models.Cookie).filter_by(domain=domain, username=username).all()
        for cookie in cookies:
            domain_cookies.append(json.loads(cookie.data))
    return domain_cookies


def set_cookies(domain: str, username: str, cookies: list):
    with db.SessionLocal() as session:
        delete_cookies(domain, username)
        for cookie in cookies:
            session.add(models.Cookie(domain=domain, username=username, data=json.dumps(cookie)))
        session.commit()


def delete_cookies(domain: str, username: str):
    with db.SessionLocal() as session:
        current_cookies = session.query(models.Cookie).filter_by(
            domain=domain,
            username=username,
        ).all()
        for cookie in current_cookies:
            session.delete(cookie)
            session.commit()
