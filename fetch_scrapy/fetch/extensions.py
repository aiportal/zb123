from scrapy import signals
from database import EventLog, ExceptionLog
from datetime import datetime, date, timedelta
import json
import sys
from wechatpy.enterprise.client import WeChatClient
from wechatpy.enterprise.client.api import WeChatMessage
import socket


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
        self.items[spider.name] = 0
        msg = '({0:2})'.format(self.count)
        EventLog.log_event(spider.name, 'OPEN', msg, info={'start': str(self.start), 'count': self.count})

    def spider_closed(self, spider, reason):
        self.count -= 1
        seconds = (datetime.now() - self.start).seconds
        items = self.items.get(spider.name, 0)
        errors = self.errors.get(spider.name, 0)
        msg = '({0:2}) seconds: {1}, items: {2}, errors: {3}'.format(self.count, seconds, items, errors)
        EventLog.log_event(spider.name, 'CLOSE', msg,
                           info={'start': str(self.start), 'count': self.count, 'reason': str(reason),
                                 'seconds': seconds, 'items': items, 'errors': errors})

        if self.count < 1:
            self.send_stat_msg()

    def item_scraped(self, item, spider):
        self.items[spider.name] = self.items.get(spider.name, 0) + 1

    def spider_error(self, failure, response, spider):
        self.errors[spider.name] = self.errors.get(spider.name, 0) + 1
        ExceptionLog.log_exception(spider.name, 'ERROR', response.url, info={
            'meta': response.meta,
            'failure': str(failure)
        })

    def send_stat_msg(self):
        if __debug__:
            return
        # 发送结果统计
        wx_company = WeChatClient('wx2c67ebb55a4012c3',
                                  'dFtHnrP3gBqIwj0aEmaRxyTlgQhg1caMWVQXW1HykiaGQ3Qpk-KIOUtF27G1IDQ5')
        wx_msg = WeChatMessage(wx_company)

        head = ['[scrapy] {0}'.format(socket.gethostname()),
                '{0:%Y-%m-%d %H:%M}'.format(self.start),
                '{0}'.format((datetime.now()-self.start)),
                '']
        items = [(k, v, self.errors.get(k, 0)) for k, v in self.items.items()]
        items = sorted(items, key=lambda x: x[2] * 10000 + int(x[1]), reverse=True)
        stat = ['{2:3} err, {1:3} item, {0:>15}'.format(k, v, e)
                for k, v, e in items]
        msg = '\n'.join(head + stat)
        wx_msg.send_text(10, 'bfbd', msg)
