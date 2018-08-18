import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class neimenggu_1Spider(scrapy.Spider):
    """
    @title: 内蒙古自治区政府采购网
    @href: http://www.nmgp.gov.cn/
    """
    name = 'neimenggu/1'
    alias = '内蒙古'
    allowed_domains = ['nmgp.gov.cn']
    start_urls = [
        ('http://www.nmgp.gov.cn/procurement/pages/tender.jsp?type=0', '招标公告/政府采购'),
        ('http://www.nmgp.gov.cn/procurement/pages/tender.jsp?type=2', '中标公告/政府采购'),
        ('http://www.nmgp.gov.cn/procurement/pages/tender.jsp?type=1', '更正公告/政府采购'),
        ('http://www.nmgp.gov.cn/procurement/pages/tender.jsp?type=4', '废标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='table.recordlist tr > td > a',
                                       attrs_xpath={'text': './/text()', 'end': '../../td[last()]//text()',
                                                    'tags': '../font//text()'})

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
        body = response.css('#wrapper') # or response.css('table.qryTable')
        tags = [s.strip() for s in data.get('tags', '').strip('[]').split('|')] + ['', '']

        day = FieldExtractor.date(data.get('end'), response.css('div.yzhang'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, tags[1]])
        g.set(subject=[data.get('subject')])
        g.set(industry=[tags[0]])
        g.set(budget=FieldExtractor.money(body))
        return [g]
