import email
import imaplib
import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from pb_design_parsers import db_tools


def parse(username, mail_username, mail_password, imap_setver, folder):
    mail = imaplib.IMAP4_SSL(imap_setver)
    mail.login(mail_username, mail_password)
    mail.select(folder)
    _, data = mail.uid('search', None, 'ALL')

    mails = []
    email_uids = data[0].split()
    for email_uid in email_uids:
        _, data = mail.uid('fetch', email_uid, '(RFC822)')
        mails.append(data)
        mail.store(email_uid, '+FLAGS', '\\Deleted')
    email_messages = []
    for mail in mails:
        email_messages.append(email.message_from_bytes(mail[0][1]))

    soups = []
    for email_message in email_messages:
        for email_part in email_message.walk():
            content = email_part.get_payload(decode=True)
            if content:
                soups.append(BeautifulSoup(email_part.get_payload(decode=True), 'lxml'))
                break
    products = []
    for soup in soups:
        raw_date = re.search(r'(?<=--)\d{2}\.\d{2}\.\d{4}(?=,)', soup.text).group(0)
        _, month, year = raw_date.split('.')
        date = datetime.fromisoformat(f'{year}-{month}-1').date() - timedelta(days=1)
        rows = soup.find_all('tr')[1:-1]
        for row in rows:
            cells = row.find_all('td')
            cells = list(map(lambda x: x.span.text, cells))
            product_name, amount, _, _, earnings = cells
            amount = int(amount)
            earnings = int(float(earnings) * 100)
            products.append((date, product_name, amount, earnings))

    for product in products:
        date, product_name, amount, earnings = product
        earnings_per_sale = earnings // amount
        remainder = earnings % amount
        for _ in range(amount):
            db_tools.add_sale(
                date=date,
                earnings=earnings_per_sale + remainder,
                product=product_name,
                reffered=False,
                market_place_domain='designcuts.com',
                username=username,
            )
            remainder = 0
