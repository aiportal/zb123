from scrapy.exceptions import IgnoreRequest
from database import JobIndex, ExceptionLog


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

