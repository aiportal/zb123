import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class guizhou_1Spider(scrapy.Spider):
    """
    @title: 贵州省政府采购网
    @href: http://www.ccgp-guizhou.gov.cn/
    """
    name = 'guizhou/1'
    alias = '贵州'
    allowed_domains = ['ccgp-guizhou.gov.cn']
    start_urls = [
        ('http://www.ccgp-guizhou.gov.cn/list-{}.html'.format(k), v)
        for k, v in [
            ('1153418052184995', '招标公告/省级'),
            ('1153454200156791', '更正公告/省级'),
            ('1153531755759540', '中标公告/省级'),
            # ('1153488085289816', '其他公告/废标公告/省级'),
            ('1153797950913584', '招标公告/市县'),
            ('1153905922931045', '中标公告/市县'),
            ('1153817836808214', '更正公告/市县'),
            # ('1153845808113747', '其他公告/废标公告/市县'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='div.xnrx > ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span[last()]//text()'})

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
        body = response.css('#info') or response.xpath('//div[@style="xnrx"]')

        day = FieldExtractor.date(data.get('day', '').replace('.', '-'))
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
