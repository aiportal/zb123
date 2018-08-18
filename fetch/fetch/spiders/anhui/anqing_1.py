import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class anqing_1Spider(scrapy.Spider):
    """
    @title: 安庆市公共资源交易服务网
    @href: http://www.aqzbcg.org/front/
    """
    name = 'anhui/anqing/1'
    alias = '安徽/安庆'
    allowed_domains = ['aqzbcg.org']
    start_urls = [
        ('http://www.aqzbcg.org/Front/ztbzx/029002/029002001/029002001003/', '招标公告/建设工程'),
        ('http://www.aqzbcg.org/Front/ztbzx/029002/029002001/029002001004/', '中标公告/建设工程'),
        ('http://www.aqzbcg.org/Front/ztbzx/029002/029002002/029002002003/', '招标公告/政府采购'),
        ('http://www.aqzbcg.org/Front/ztbzx/029002/029002002/029002002004/', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.MsoNormalTable, #filedown')

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
