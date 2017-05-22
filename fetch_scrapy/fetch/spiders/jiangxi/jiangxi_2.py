import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class jiangxi_2Spider(scrapy.Spider):
    """
    @title: 江西建设工程招标投标网
    @href: http://www.jxjszbtb.com/jxjsztbw/
    """
    name = 'jiangxi/2'
    alias = '江西'
    allowed_domains = ['jxjszbtb.com']
    start_urls = [
        ('http://www.jxjszbtb.com/jxjsztbw/zbgg/', '招标公告/建设工程'),
        ('http://www.jxjszbtb.com/jxjsztbw/zbgs/', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.right-area-content a.WebList_sub',
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
        body = response.css('#TDContent, #trAttach')

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
