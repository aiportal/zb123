from scrapy import signals
from database import EventLog, ExceptionLog
from datetime import datetime, date, timedelta
import socket
import peewee


class CrawlerStatisticExtension(object):
    """
    Statistic spider's errors and items.
    """
    stats = {}

    def __init__(self, name: str):
        self.name = name
        self.start = datetime.now()
        self.end = None
        self.reason = None
        self.errors = 0
        self.items = 0

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls(crawler.spidercls.name)
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext

    def spider_opened(self, spider):
        type(self).stats[spider.name] = self
        msg = '({0:3}) {1}'.format(self.running_count(), spider.name)
        EventLog.log_event(spider.name, 'OPEN', msg)

    def item_scraped(self, item, spider):
        self.items += 1

    def spider_error(self, failure, response, spider):
        self.errors += 1

    def spider_closed(self, spider, reason):
        self.end = datetime.now()
        self.reason = reason

        seconds = (self.end - self.start).seconds
        msg = '({0:3}) seconds: {1}, items: {2}, errors: {3}'\
            .format(self.running_count(), seconds, self.items, self.errors)
        EventLog.log_event(spider.name, 'CLOSE', msg)

        self.send_statistic()
        self.send_exceptions()

    @classmethod
    def running_count(cls):
        return len([x for x in cls.stats.values() if not x.end])

    @classmethod
    def send_statistic(cls):
        if cls.running_count() > 0:
            return

        items = sorted(cls.stats.values(), key=lambda x: '{0.errors:3}/{0.items:3}/{0.name}'.format(x), reverse=True)
        start = min([x.start for x in items])
        delta = str(datetime.now() - start)[:4]
        count = sum([x.items for x in items])
        head = [
            '主机：{}'.format(socket.gethostname()),
            '启动：{:%H:%M   [%m-%d]}'.format(start),
            '耗时：{}'.format(delta),
            '总数：{}'.format(count),
        ]
        body = ['{0.errors:3}, {0.items:3}, {0.name:>15}'.format(x) for x in items]
        cls.send_wechat_msg(head, body)

    @classmethod
    def send_exceptions(cls):
        items = cls.stats.values()

        start = min([x.start for x in items])
        exceptions = ExceptionLog.select(ExceptionLog.source, peewee.fn.COUNT(ExceptionLog.ID).alias('count'))\
            .where(ExceptionLog.time >= start)\
            .where(ExceptionLog.level != 'main')\
            .group_by(ExceptionLog.source)
        count = sum([x.count for x in exceptions])

        errors = [x for x in items if x.reason != 'finished']
        errors = sorted(errors, key=lambda x: x.reason)

        head = [
            '主机：{}'.format(socket.gethostname()),
            '异常：{}'.format(count),
        ]
        body = ['{0.count:3} {0.source:>15}'.format(x) for x in exceptions] + \
               ['{0.reason} {0.name}'.format(x) for x in errors]
        cls.send_wechat_msg(head, body)

    @staticmethod
    def send_wechat_msg(head: list, body: list):
        from wechatpy.enterprise.client import WeChatClient
        from wechatpy.enterprise.client.api import WeChatMessage

        thumb_media_id = '1C3cuJV5r_RqUo4R_t3MePj7QjPaFusQwfwSgOfGNtSYnp9Dy3u9sfoeI3nZgEm_3tAdE-pu5t5LOa-gZ5DjmzA'
        wx_company = WeChatClient('wx2c67ebb55a4012c3',
                                  'dFtHnrP3gBqIwj0aEmaRxyTlgQhg1caMWVQXW1HykiaGQ3Qpk-KIOUtF27G1IDQ5')

        wx_msg = WeChatMessage(wx_company)
        msg = '\n'.join(head + [''] + body)
        if len(msg.encode()) < 2048:
            wx_msg.send_text(10, 'bfbd', msg)
            return

        title = '[scrapy] {}'.format(socket.gethostname())
        digest = '\n'.join(head)
        content = '<br/>'.join(head + [''] + body)
        wx_msg.send_mp_articles(10, 'bfbd', [{
            'thumb_media_id': thumb_media_id,
            'author': None,
            'title': title,
            'content': content,
            'content_source_url': None,
            'digest': digest,
            'show_cover_pic': 0,
        }])

