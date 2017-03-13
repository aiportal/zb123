from scrapy import signals
from database import EventLog, ExceptionLog
from datetime import datetime, timedelta
import json
import sys


# Spider 运行异常日志
class ExceptionLogExtension(object):

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext

    def spider_error(self, failure, response, spider):
        ExceptionLog.log_exception(spider.name, 'ERROR', response.url,
                                   info={'meta': response.meta, 'exception': str(failure)})
        spider.logger.error('failure at: ' + response.url)
        spider.logger.error('failure info: ' + str(failure))


# Spider 运行统计日志
class SpiderStatsExtension(object):
    def __init__(self):
        self.start = datetime.now()
        self.args = sys.argv
        self.count = 0
        self.items = {}
        self.errors = {}

    @classmethod
    def from_crawler(cls, crawler):
        if not hasattr(cls, '__instance'):
            setattr(cls, '__instance', cls())
        ext = getattr(cls, '__instance')
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        return ext

    def spider_opened(self, spider):
        self.count += 1
        EventLog.log_event(spider.name, 'OPEN', info={'start': str(self.start), 'count': self.count})

    def spider_closed(self, spider, reason):
        self.count -= 1
        seconds = (datetime.now() - self.start).seconds
        items = self.items.get(spider.name, 0)
        errors = self.errors.get(spider.name, 0)
        msg = '({0:2}) seconds: {1}, items: {2}, errors: {3}'.format(self.count, seconds, items, errors)
        EventLog.log_event(spider.name, 'CLOSE', msg,
                           info={'start': str(self.start), 'count': self.count, 'reason': str(reason),
                                 'seconds': seconds, 'items': items, 'errors': errors})

    def item_scraped(self, item, spider):
        self.items[spider.name] = self.items.get(spider.name, 0) + 1

    def spider_error(self, failure, response, spider):
        self.errors[spider.name] = self.errors.get(spider.name, 0) + 1
