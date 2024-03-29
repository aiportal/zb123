import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class hainan_2Spider(scrapy.Spider):
    """
    @title: 海南省招投标监管网
    @href: http://ztb.hainan.gov.cn/index.php
    """
    name = 'hainan/2'
    alias = '海南'
    allowed_domains = ['hainan.gov.cn']
    start_urls = [
        ('http://ztb.hainan.gov.cn/zbgg/list.php?zb=1', '招标公告/建设工程'),
        ('http://ztb.hainan.gov.cn/zbjg/', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='.ny_news ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.ny_wz')
        suffix = '（\w{2,5}）$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(suffix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
