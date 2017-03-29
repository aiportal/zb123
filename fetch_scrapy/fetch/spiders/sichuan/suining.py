import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class SuiNingSpider(scrapy.Spider):
    """
    @title: 遂宁市公共资源交易服务中心
    @host: http://www.snjsjy.com/
    """
    name = 'sichuan/suining'
    alias = '四川/遂宁'
    start_urls = [
        ('http://www.snjsjy.com/Content/Cloud/265,268_1_20_0', '招标信息/建设工程'),
        ('http://www.snjsjy.com/Content/Cloud/267_1_20_0', '中标信息/建设工程'),
        ('http://www.snjsjy.com/Content/Cloud/29_1_20_0', '招标信息/政府采购'),
        ('http://www.snjsjy.com/Content/Cloud/31_1_20_0', '中标信息/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('div.box-text-list > ul > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../span[1]//text()'})
    page_extractor = MetaLinkExtractor(css=('div.pager a:contains(下一页)',))

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pages = self.page_extractor.links(response)
        if pages:
            yield scrapy.Request(pages[0].url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.xx_content') or response.css('div.notice-detail') \
            or response.css('div.container') or response.css('div.cphMiddle_divAttach') \
            # or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#cphMiddle_lblCount'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('#cphMiddle_pTitle'))
        title = re.sub('^\w{3}\s+', '', title or '')
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
