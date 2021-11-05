from apscheduler.schedulers.blocking import BlockingScheduler

from loguru import logger
import requests
import os
from pb_design_parsers import creative, envanto


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
def parse_creative_market():
    logger.info('Start parsing cm')
    creative.parse(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    creative.parse(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))


@sched.scheduled_job('cron', hour=2, minute=0)
@logger.catch
def parse_elements():
    logger.info('Start parsing elements')
    envanto.parse(os.environ.get('ELEM_USER'), os.environ.get('ELEM_USER_PASS'))


@sched.scheduled_job('cron', hour=15, minute=19)
@logger.catch
def parse_cm_items():
    logger.info('Start parsing creative items')
    creative.refresh_products(os.environ.get('CM_USER'), os.environ.get('CM_USER_PASS'))
    creative.refresh_products(os.environ.get('CM_USER_1'), os.environ.get('CM_USER_PASS_1'))


if __name__ == "__main__":
    logger.add(sink=send_tg_alarm)
    sched.start()
