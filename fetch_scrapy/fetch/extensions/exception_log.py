from scrapy import signals
from database import EventLog, ExceptionLog


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
