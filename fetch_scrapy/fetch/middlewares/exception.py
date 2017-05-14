import scrapy
from database import ExceptionLog


class ExceptionMiddleware(object):
    @staticmethod
    def process_exception(request, exception, spider):
        ExceptionLog.log_exception(spider.name, 'HTTP', request.url,
                                   info={'meta': request.meta, 'exception': str(exception)})

    @staticmethod
    def process_spider_exception(response, exception, spider):
        redirects = response.request.meta.get('redirect_urls', [])
        req_url = redirects and redirects[0] or response.url            # 原始请求网址
        ExceptionLog.log_exception(spider.name, 'SPIDER', req_url, info={
            'meta': response.meta, 'exception': str(exception), 'status': response.status
        })
