import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class wuhai_1Spider(scrapy.Spider):
    """
    @title: 乌海市公共资源交易中心
    @href: http://www.whggzy.com/index!index.action
    """
    name = 'neimenggu/wuhai/1'
    alias = '内蒙古/乌海'
    allowed_domains = ['whggzy.com']
    start_urls = [
        ('http://www.whggzy.com/articleWeb!list.action?resourceCode=cgzbgg', '招标公告/政府采购'),
        ('http://www.whggzy.com/articleWeb!list.action?resourceCode=cgzbgs', '中标公告/政府采购'),
        ('http://www.whggzy.com/articleWeb!list.action?resourceCode=jszbgg', '招标公告/建设工程'),
        ('http://www.whggzy.com/articleWeb!list.action?resourceCode=jszbgs', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='table.in_ullist tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('div.newsdetail_con > *')

        day = FieldExtractor.date(data.get('day') or response.css('div.newsdetail_tool'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
