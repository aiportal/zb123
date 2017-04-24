import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class NmgBaotou1Spider(scrapy.Spider):
    """
    @title: 
    @href:
    """
    name = 'neimenggu/baotou/1'
    alias = '内蒙古/包头'
    allowed_domains = ['btzfcg.gov.cn']
    start_urls = [
        ('http://www.btzfcg.gov.cn/portal/topicView.do?method=view&view=stockBulletin&id={}&ver=2'.format(k), v)
        for k, v in [
            ('1660', '招标公告/市级'),
            ('2014', '中标公告/市级'),
            ('1663', '更正公告/市级'),
            ('1662', '招标公告/县级'),
            ('1664', '中标公告/县级'),
            ('1666', '更正公告/县级'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#topicChrList_20070702_table tbody > tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]/text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#bulletinContent')

        day = FieldExtractor.date(data.get('day'))
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
