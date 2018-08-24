import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class henan_1Spider(scrapy.Spider):
    """
    @title: 河南省政府采购网
    @href: http://www.hngp.gov.cn/
    """
    name = 'henan/1'
    alias = '河南'
    allowed_domains = ['hngp.gov.cn']
    start_urls = [
        ('http://www.hngp.gov.cn/henan/ggcx?appCode=H60&channelCode=0101&pageSize=20', '招标公告/采购公告'),
        ('http://www.hngp.gov.cn/henan/ggcx?appCode=H60&channelCode=0102&pageSize=20', '中标公告'),
        ('http://www.hngp.gov.cn/henan/ggcx?appCode=H60&channelCode=0103&pageSize=20', '更正公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.List2 ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#content')

        day = FieldExtractor.date(data.get('day'), response.css('span.Blue:contains("2017")'))
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
