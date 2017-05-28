import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from urllib.parse import urljoin
import sys
from database.link import SiteInfo
from urllib.parse import urlsplit, urljoin


class SiteLinksSpider(scrapy.Spider):
    """ crawl sites links """

    name = 'links'
    start_urls = [
        # 'http://ggzyjy.jl.gov.cn/jilinztb/',
        'http://www.lzgpc.gov.cn/ceinwz/indexnewlz.htm',
        'http://lsggzy.com.cn/tpfront/',
    ]
    disabled_urls = [
        'www.sina.com.cn',
        'www.baidu.com.cn',
    ]
    custom_settings = {'DEPTH_LIMIT': 5}

    links_extractor = NodesExtractor(xpath='//a', attrs_xpath={'text': './/text()'})
    options_extractor = NodesExtractor(xpath='//option', attrs_xpath={'text': './/text()'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        query = SiteInfo.select(SiteInfo.id, SiteInfo.url, SiteInfo.enabled)
        start_urls = [x.url for x in query if x.enabled]
        disabled_urls = [x.url for x in query if not x.enabled]
        if not self.start_urls:
            self.start_urls = start_urls
        if disabled_urls:
            self.disabled_urls = disabled_urls

    def start_requests(self):
        if 'links' not in sys.argv:
            return []
        for url in self.start_urls:
            yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        if b'text/html' not in response.headers['Content-Type']:
            return []

        host = urlsplit(response.url).hostname

        links = [(x['href'], x.get('title') or x['text'])
                 for x in self.links_extractor.extract_nodes(response)
                 if urlsplit(x.get('href', '')).hostname]

        options = [(x['value'], x['text'])
                   for x in self.options_extractor.extract_nodes(response)
                   if urlsplit(x.get('value', '')).hostname]

        sites = [(url, text) for url, text in links + options
                 if urlsplit(url).hostname != host
                 and urlsplit(url).hostname not in self.disabled_urls]

        # append site
        site_id = None
        if 'name' in response.meta:
            parent = response.meta['parent']
            title = FieldExtractor.text(response.css('title'))
            ttl = int(response.meta['download_latency'] * 1000)
            site_id = SiteInfo.append(url=response.url, title=title, ttl=ttl, parent=parent)

        for row in sites:
            url = row[0].strip('/')
            if not url.startswith('http'):
                url = 'http://' + url
            yield scrapy.Request(url, meta={'name': row[1], 'parent': site_id}, dont_filter=True)
