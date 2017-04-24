import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class JiangsuChangzhou2Spider(scrapy.Spider):
    """
    @title: 常州市建设工程交易网
    @href: http://www.czzbb.net/czztb/
    """
    name = 'jiangsu/changzhou/2'
    alias = '江苏/常州'
    allowed_domains = ['czzbb.net']
    start_urls = [
        ('http://www.czzbb.net/czztb/jyxx/010001/', '招标公告'),
        ('http://www.czzbb.net/czztb/jyxx/010002/', '中标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(
        xpath='//td[@background="/czztb/webimages/sub_01_bg.gif"]/../..//a[@target="_blank"]',
        attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'}
    )

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#spnShow') or response.css('#TDContent') or response.css('epointform')
        prefix = '^\[\w+\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
