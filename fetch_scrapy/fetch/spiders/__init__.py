# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import scrapy
from scrapy.http.headers import Headers
from itertools import repeat, product
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit
import uuid

from database import JobIndex
from fetch.items import GatherItem
from fetch.extractors import *


class SpiderHelper(object):
    @staticmethod
    def replace_url_param(url, **kwargs):
        scheme, netloc, path, query, fragment = urlsplit(url)
        params = parse_qs(query)
        for k, v in kwargs.items():
            params[k] = str(v)
        query = urlencode(params, True)
        return urlunsplit((scheme, netloc, path, query, fragment))

    @staticmethod
    def join_words(*args):
        values = [str(v).strip() for v in args if v and str(v).strip()]
        return '/'.join(values)

    @staticmethod
    def url_exists(url):
        return JobIndex.url_exists(url)

    @staticmethod
    def iter_params(params: dict):
        """ 遍历参数组合 """
        params = {k: isinstance(v, dict) and v or {str(v): None} for k, v in params.items()}
        params = [list(zip(repeat(k), v.items())) for k, v in params.items()]
        for param in [list(i) for i in product(*params)]:
            data = {}
            meta = {}
            for k, (v, m) in param:     # key, value, meta in param
                data[k] = v
                meta[k] = m or v
            yield data, meta


class BaseSpider(scrapy.Spider, SpiderHelper):
    """ 所有Spider的基类"""

    # 索引页的引用页
    start_referer = None

    # 索引页的参数组合
    start_params = {}

    def start_requests(self):
        headers = Headers(self.start_referer and {'Referer': self.start_referer} or {})
        url = self.start_urls[0]
        for req in self._requests_from_params(url, self.start_params):
            req.headers = headers
            self.logger.info('start params: ' + req.url)
            yield req
        for url in self.start_urls[1:]:
            self.logger.info('start url: ' + url)
            yield scrapy.Request(url, headers=headers, dont_filter=True)

    # 枚举所有的参数组合，生成Request
    @staticmethod
    def _requests_from_params(url, params: dict):
        url += ('?' not in url and '?' or '&')
        params = {k: isinstance(v, dict) and v or {str(v): None} for k, v in params.items()}
        params = [list(zip(repeat(k), v.items())) for k, v in params.items()]
        for param in [list(i) for i in product(*params)]:
            data = {}
            meta = {}
            for k, (v, m) in param:
                data[k] = v
                meta[k] = m or v
            request_url = url + (data and urlencode(data) or '')
            yield scrapy.Request(request_url, meta={'params': meta}, dont_filter=True)

    def parse(self, response):
        yield from super().parse(response)

    def gather_item(self, response):
        """ 解析 GatherItem 对象的基本属性"""

        # 用请求网址的hash做主键
        source = self.name.split('/')[0]
        url = response.meta.get('top_url') or self._request_url(response)
        url_hash = JobIndex.url_hash(url)

        g = GatherItem(source=source, url=url, uuid=url_hash)
        g['html'] = None
        g['real_url'] = response.url == url and None or response.url
        g['top_url'] = response.meta.get('top_url')
        g['index_url'] = response.meta.get('index_url') or response.request.headers.get('Referer', '').decode()
        return g

    def _request_url(self, response):
        redirects = response.request.meta.get('redirect_urls', [])
        return redirects and redirects[0] or response.url


class HtmlMetaSpider(BaseSpider):
    """ extend this class if index page is html.
    don't override <parse> function if you can implement stop by skip count logic.
    you can override <link_requests> and <page_requests> functions to custom link and page parse.
    """
    # 索引页网址解析（获取详情页网址）
    link_extractor = None

    # 索引页翻页解析
    page_extractor = None

    @property
    def max_skip(self):
        return self.crawler.settings.getint('MAX_SKIP')

    def parse(self, response):
        for req in self.link_requests(response):
            if not self.url_exists(req.url):
                req.callback = self.parse_item
                yield req
            else:
                response.meta['skip_count'] = response.meta.get('skip_count', 0) + 1
        # check skip count to stop
        skip_count = response.meta.get('skip_count', 0)
        self.logger.info('skip count: ' + str(skip_count))
        if skip_count < self.max_skip:
            for req in self.page_requests(response):
                req.headers = Headers(self.start_referer and {'Referer': self.start_referer} or {})
                self.logger.info('next page: ' + req.url)
                yield req

    def link_requests(self, response):
        for link in self.link_extractor.extract_links(response):
            data = dict(link.meta, **response.meta['params'])
            yield scrapy.Request(link.url, meta={'data': data})

    def page_requests(self, response):
        next_page = [p for p in self.page_extractor.extract_links(response)]
        if next_page:
            yield scrapy.Request(next_page[0].url, meta=response.meta)

    def parse_item(self, response):
        raise NotImplementedError()


class JsonMetaSpider(BaseSpider):
    """ extend this class if index data is json.
    """
    # 详情页网址生成器
    link_generator = None

    # 翻页网址生成器
    page_generator = None

    @property
    def max_skip(self):
        return self.crawler.settings.getint('MAX_SKIP')

    def parse(self, response):
        for req in self.link_requests(response):
            if not self.url_exists(req.url):
                req.callback = self.parse_item
                yield req
            else:
                response.meta['skip_count'] = response.meta.get('skip_count', 0) + 1
                self.logger.info('skip: ' + req.url)
        # check skip_count to stop.
        skip_count = response.meta.get('skip_count', 0)
        self.logger.info('skip count: ' + str(skip_count))
        if skip_count < self.max_skip:
            for req in self.page_requests(response):
                req.headers = Headers(self.start_referer and {'Referer': self.start_referer} or {})
                self.logger.info('next page: ' + req.url)
                yield req

    def link_requests(self, response):
        for link in self.link_generator.generate_links(response):
            meta = {'data': dict(link.data, **response.meta['params']), 'top_url': link.ref_url, 'index_url': link.index_url}
            headers = {'Referer': link.ref_url or link.index_url}
            yield scrapy.Request(link.url, meta=meta, headers=headers, callback=self.parse_item)

    def page_requests(self, response):
        page_url = self.page_generator.generate_page(response)
        if page_url:
            yield scrapy.Request(page_url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        raise NotImplementedError()
