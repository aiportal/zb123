import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class fujian_3Spider(scrapy.Spider):
    """
    @title: 福建省建设工程交易网
    @href: http://www.fjjsjy.com/
    """
    name = 'fujian/3'
    alias = '福建'
    allowed_domains = ['fjjsjy.com']
    start_urls = [
        ('http://www.fjjsjy.com/Front/zbgg', '招标公告/建设工程', 0),
        ('http://www.fjjsjy.com/Front/ZBProxy_List/zbgs', '中标公告/建设工程', 1),
    ]

    link_extractors = (
        MetaLinkExtractor(css='#div_Li1 tr > td:nth-child(1) > a',
                          attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'}),
        MetaLinkExtractor(css='#div_001 tr > td:nth-child(1) > a',
                          attrs_xpath={'text': './/text()', 'day': '../../td[4]//text()'}),
    )

    def start_requests(self):
        for url, subject, extractor in self.start_urls:
            data = dict(subject=subject, extractor=extractor)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        extractor = self.link_extractors[response.meta['data']['extractor']]
        links = extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.DetailTable')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
