import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shaanxi_1Spider(scrapy.Spider):
    """
    @title: 陕西省政府采购
    @href: http://www.ccgp-shaanxi.gov.cn/index.jsp
    """
    name = 'shaanxi/1'
    alias = '陕西'
    allowed_domains = ['ccgp-shaanxi.gov.cn']
    start_urls = [
        ('http://www.ccgp-shaanxi.gov.cn/saveData.jsp?ClassBID={}&type=AllView'.format(k), v)
        for k, v in [
            ('C0001', '招标公告/政府采购/省级'),
            ('C0002', '中标公告/政府采购/省级'),
            ('D0003', '预公告/询价公告/政府采购/省级'),
            ('FB001', '废标公告/政府采购/省级'),
            ('E0001', '更正公告/政府采购/省级'),
        ]
    ] + [
        ('http://www.ccgp-shaanxi.gov.cn/saveDataDq.jsp?ClassBID={}&type=AllViewDq'.format(k), v)
        for k, v in [
            ('C0001', '招标公告/政府采购/市县'),
            ('C0002', '中标公告/政府采购/市县'),
            ('D0003', '预公告/询价公告/政府采购/市县'),
            ('FB001', '废标公告/政府采购/市县'),
            ('E0001', '更正公告/政府采购/市县'),
        ]
    ]
    custom_settings = {'COOKIES_ENABLED': True}

    link_extractor = MetaLinkExtractor(css='table.tab tr > td > a.b',
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
        body = response.css('td.SaleT01')
        # detail_title = FieldExtractor.text(response.css('table.td span.SaleT01'))

        day = FieldExtractor.date(data.get('day'))
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
