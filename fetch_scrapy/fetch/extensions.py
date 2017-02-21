from scrapy import signals
from database import EventLog
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
        err = EventLog(source=spider.name, url=response.url, level='ERROR')
        err.status = 6001
        err.info = str(failure)
        err.data = json.dumps(response.meta, ensure_ascii=False)
        err.save()
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
        data = {
            'spider': spider.name,
            'alias': spider.alias,
            'args': self.args,
            'start': str(self.start),
        }
        self.count += 1
        url = '({1:02}) {0}'.format(spider.name, self.count)
        evt = EventLog(source='statistics', url=url, level='OPEN', status=1101)
        evt.info = spider.name
        evt.data = json.dumps(data, ensure_ascii=False)
        evt.save()

    def spider_closed(self, spider, reason):
        data = {
            'spider': spider.name,
            'alias': spider.alias,
            'items': self.items,
            'errors': self.errors,
            'args': self.args,
            'start': str(self.start),
            'stop': str(datetime.now()),
        }
        self.count -= 1
        url = '({1:02}) {0}: {2} seconds'.format(spider.name, self.count, (datetime.now() - self.start).seconds)
        evt = EventLog(source='statistics', url=url, level='CLOSE', status=1102)
        evt.info = '{0} items: {1}, errors: {2}'.format(
            spider.name, self.items.get(spider.name, 0), self.errors.get(spider.name, 0))
        evt.data = json.dumps(data, ensure_ascii=False)
        evt.save()

    def item_scraped(self, item, spider):
        self.items[spider.name] = self.items.get(spider.name, 0) + 1

    def spider_error(self, failure, response, spider):
        self.errors[spider.name] = self.errors.get(spider.name, 0) + 1
