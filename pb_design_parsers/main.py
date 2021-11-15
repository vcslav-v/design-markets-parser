from apscheduler.schedulers.blocking import BlockingScheduler

from loguru import logger
import requests
import os
from pb_design_parsers import creative, envanto, yellowimgs


sched = BlockingScheduler()


def send_tg_alarm(message):
    requests.post(
            'https://api.telegram.org/bot{token}/sendMessage?chat_id={tui}&text={text}'.format(
                token=os.environ.get('ALLERT_BOT_TOKEN'),
                tui=os.environ.get('ADMIN_TUI'),
                text=message,
            ))


@sched.scheduled_job('cron', hour=1, minute=0)
@logger.catch
def parse_marketы():
    logger.info('Start parsing')
    creative.parse(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    creative.parse(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))
    envanto.parse(os.environ.get('ELEM_USER'), os.environ.get('ELEM_USER_PASS'))
    yellowimgs.parse(os.environ.get('YIM_USER'), os.environ.get('YIM_USER_PASS'))


@sched.scheduled_job('cron', day_of_week=0, hour=3)
@logger.catch
def parse_items():
    logger.info('Start parsing items')
    creative.refresh_products(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    creative.refresh_products(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))
    envanto.refresh_products(os.environ.get('ELEM_USER'), os.environ.get('ELEM_USER_PASS'))


@sched.scheduled_job('cron', hour=11, minute=6)
@logger.catch
def parse_elements_items():
    logger.info('TEST')
    yellowimgs.refresh_products(os.environ.get('YIM_USER'), os.environ.get('YIM_USER_PASS'))


if __name__ == "__main__":
    logger.add(sink=send_tg_alarm)
    sched.start()
