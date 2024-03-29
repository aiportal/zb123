import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class AnhuiMaanshan1Spider(scrapy.Spider):
    """
    @title: 马鞍山公共资源交易中心
    @href: http://zbcg.mas.gov.cn/maszbw
    """
    name = 'anhui/maanshan/1'
    alias = '安徽/马鞍山'
    allowed_domains = ['mas.gov.cn']
    start_urls = [
        ('http://zbcg.mas.gov.cn/maszbw/jygg/028001/028001001/', '招标公告/建设工程'),
        ('http://zbcg.mas.gov.cn/maszbw/jygg/028001/028001003/', '中标公告/建设工程'),
        ('http://zbcg.mas.gov.cn/maszbw/jygg/028002/028002001/', '招标公告/政府采购'),
        ('http://zbcg.mas.gov.cn/maszbw/jygg/028002/028002003/', '中标公告/政府采购'),
        ('http://zbcg.mas.gov.cn/maszbw/jygg/028007/', '预公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="18"] > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data, 'proxy': True}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent, .infodetail')
        suffix = '（皖[A-Z0-9-]+）$'

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
