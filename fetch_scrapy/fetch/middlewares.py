from scrapy.exceptions import IgnoreRequest
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from database import EventLog
import json


# HTTP请求异常时记录信息
class HttpExceptionMiddleware(object):
    def process_exception(self, request, exception, spider):
        e = EventLog(source=spider.name, url=request.url, level='HTTP', status=5001)
        e.info = str(exception)
        e.data = json.dumps(request.meta, ensure_ascii=False)
        e.save()
        spider.logger.error('HTTP exception at: ' + request.url)


# 服务器返回空值时重试
class EmptyRetryMiddleware(object):

    def __init__(self, settings):
        self.max_retry_times = settings.getint('RETRY_TIMES')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_response(self, request, response, spider):
        if len(response.body) > 0:
            return response
        retry = request.meta.get('retry_times', 0) + 1
        if retry <= self.max_retry_times:
            req = request.copy()
            req.meta['retry_times'] = retry
            req.dont_filter = True
            spider.logger.warning('retry: {0} for {1} times.'.format(req.url, retry))
            return req
        else:
            e = EventLog(source=spider.name, url=response.url, level='RETRY', status=5002)
            e.info = 'retry {0} times fail.'.format(retry)
            e.data = json.dumps(request.meta, ensure_ascii=False)
            e.save()
            spider.logger.error('RETRY max fails for: ' + request.url)
            raise IgnoreRequest(e.info)


# 解析异常时记录
class SpiderExceptionMiddleware(object):
    def process_spider_exception(self, response, exception, spider):
        e = EventLog(source=spider.name, url=response.url, level='SPIDER', status=response.status)
        e.info = str(exception)
        e.data = json.dumps(response.meta, ensure_ascii=False)
        e.save()
        spider.logger.error('SPIDER exception for: ' + response.url)
