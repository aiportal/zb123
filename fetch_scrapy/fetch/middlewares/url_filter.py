import scrapy
from scrapy.dupefilters import BaseDupeFilter
import json
if __debug__:
    from database.local import JobIndex
else:
    from database import JobIndex


class UrlFilterMiddleware(BaseDupeFilter):
    """ request请求过滤 """
    def request_seen(self, request):
        return JobIndex.url_exists(request.url)

    def log(self, request, spider):
        form = isinstance(request, scrapy.FormRequest) and request.meta.get('data', {}) or {}
        msg = 'Url filtered: {0}, {1}'.format(request.url, json.dumps(form, ensure_ascii=False, sort_keys=True))
        spider.logger.info(msg)
