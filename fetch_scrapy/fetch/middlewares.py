from scrapy.exceptions import IgnoreRequest
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from database import ExceptionLog
import json


# 请求异常时记录信息
class HttpExceptionMiddleware(object):
    @staticmethod
    def process_exception(request, exception, spider):
        ExceptionLog.log_exception(spider.name, 'HTTP', request.url,
                                   info={'meta': request.meta, 'exception': str(exception)})
        spider.logger.error('HTTP exception at: ' + request.url)


# 解析异常时记录信息
class SpiderExceptionMiddleware(object):
    @staticmethod
    def process_spider_exception(response, exception, spider):
        ExceptionLog.log_exception(spider.name, 'SPIDER', response.url,
                                   info={'meta': response.meta, 'exception': str(exception), 'status': response.status})
        spider.logger.error('PARSE exception for: ' + response.url)


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
            ExceptionLog.log_exception(spider.name, 'RETRY', response.url, info=request.meta)
            spider.logger.warning('retry: {0} for {1} times.'.format(req.url, retry))
            return req
        else:
            ExceptionLog.log_exception(spider.name, 'RETRY_MAX', response.url, info=request.meta)
            spider.logger.error('RETRY max fails for: ' + request.url)
            raise IgnoreRequest('retry {0} times fail.'.format(retry))

