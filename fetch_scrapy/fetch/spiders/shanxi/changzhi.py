import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class ChangzhiSpider(scrapy.Spider):
    name = 'shanxi/changzhi'
    alias = '山西/长治'
    allowed_domains = ['czzc.gov.cn']
    start_urls = [
        ('http://www.czzc.gov.cn/czzcgov/caijixinxi/yugonggao/', '预公告'),
        ('http://www.czzc.gov.cn/czzcgov/caijixinxi/caijigonggao/', '招标公告'),
        ('http://www.czzc.gov.cn/czzcgov/caijixinxi/jieguogonggao/', '中标公告'),
        # ('http://www.czzc.gov.cn/czzcgov/caijixinxi/biangenggonggao/', '更正公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('tr > td > a[href$=".html"][target=_blank]',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = MetaLinkExtractor(css=('div.epages a:contains(下一页)',))

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
        body = response.css('td.content') or response.css('body > table:nth-child(4)') or response.css('body')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('Title') or data.get('text')
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
