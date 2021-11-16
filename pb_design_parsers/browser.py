from selenium import webdriver
from time import sleep
import json
import os
from urllib.parse import urlparse
from pb_design_parsers import db_tools


def get() -> webdriver.Remote:
    browser_options = webdriver.chrome.options.Options()
    browser_options.addArgument('--kiosk')
    browser_options.set_capability('browserName', 'chrome')
    browser_options.set_capability('enableVNC', True)
    browser_options.set_capability('enableVideo', False)
    browser_options.add_extension('anticaptcha.crx')
    driver = webdriver.Remote(
            command_executor=os.environ.get('DRIVER_URL'),
            options=browser_options,
        )
    driver.get('https://antcpt.com/blank.html')
    message = {
            'receiver': 'antiCaptchaPlugin',
            'type': 'setOptions',
            'options': {'antiCaptchaApiKey': os.environ.get('AC_KEY')},
        }
    sleep(10)
    driver.execute_script(
        'return window.postMessage({});'.format(json.dumps(message)),
    )
    sleep(5)
    return driver


def set_cookies(driver: webdriver.Remote, site_url: str, username: str):
    driver.get(site_url)
    domain = urlparse(site_url).netloc
    cookies = db_tools.get_cookies(domain, username)
    if cookies:
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.get(site_url)


def save_cookies(driver: webdriver.Remote, site_url: str, username: str):
    domain = urlparse(site_url).netloc
    cookies = driver.get_cookies()
    db_tools.set_cookies(domain, username, cookies)
