import scrapy
from database import JobIndex
import urllib.parse as parse


class SpiderTool:
    """ 通用工具类 """

    @classmethod
    def url_exists(cls, url):
        """ url 是否存在 """
        return JobIndex.url_exists(url)

    @classmethod
    def url_filter(cls, links: iter, key: callable=lambda x: x):
        """ 批量过滤已存在的 url """
        return [x for x in links if not cls.url_exists(key(x))]

    @staticmethod
    def url_replace(url, **kwargs):
        """ 替换url中的参数 """
        scheme, netloc, path, query, fragment = parse.urlsplit(url)
        params = parse.parse_qs(query)
        for k, v in sorted(kwargs.items()):
            params[k] = str(v)
        query = parse.urlencode(params, True)
        return parse.urlunsplit((scheme, netloc, path, query, fragment))
