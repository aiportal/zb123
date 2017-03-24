import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class HainanSpider(scrapy.Spider):
    name = 'hainan'
    alias = '海南'
    allowed_domains = ['ggzy.hi.gov.cn']
    start_urls = [
        ('http://www.ggzy.hi.gov.cn/jgzbgg/index.jhtml', '招标公告/建设工程'),
        ('http://www.ggzy.hi.gov.cn/jgzbgs/index.jhtml', '中标公告/建设工程'),
        ('http://www.ggzy.hi.gov.cn/cggg/index.jhtml', '招标公告/政府采购'),
        ('http://www.ggzy.hi.gov.cn/cgzbgg/index.jhtml', '中标公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('table.newtable > tbody > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                              'area': '../../td[2]//text()'})
    page_extractor = NodeValueExtractor(css=('div.pagesite a:contains(下一页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for link in links:
            link.meta.update(**response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        pager = SpiderTool.re_text("encodeURI\('(.+)'\)", pager)
        if pager:
            url = response.url
            url = url[:url.rfind('/')] + '/' + pager
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = response.css('div.newsCon > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area', '')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.newsCon')))
        return [g]
