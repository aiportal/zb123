import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date


class JiangsuSpider(scrapy.Spider):
    """
    @title: 江苏政府采购
    @href: http://www.ccgp-jiangsu.gov.cn/
    """
    name = 'jiangsu/1'
    alias = '江苏'
    allowed_domains = ['ccgp-jiangsu.gov.cn']
    start_urls = [
        ('http://www.ccgp-jiangsu.gov.cn/cgxx/cgyg/', '预公告/采购预告'),
        ('http://www.ccgp-jiangsu.gov.cn/cgxx/cggg/', '招标公告/采购公告'),
        ('http://www.ccgp-jiangsu.gov.cn/cgxx/cjgg/', '中标公告/成交公告'),
        ('http://www.ccgp-jiangsu.gov.cn/cgxx/gzgg/', '更正公告'),
        ('http://www.ccgp-jiangsu.gov.cn/cgxx/xqyj/', '预公告/征求意见'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data, 'proxy': True}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.list_list ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.detail_con')

        day = FieldExtractor.date(data.get('day'), response.css('div.detail_bz'), date.today())
        title = data.get('title') or data.get('text')
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
