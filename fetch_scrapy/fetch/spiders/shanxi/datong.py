import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class DatongSpider(scrapy.Spider):
    name = 'shanxi/datong'
    alias = '山西/大同'
    allowed_domains = ['dtgpc.gov.cn']
    start_urls = [
        ('http://www.dtgpc.gov.cn/portal/netzfcg/gglist.aspx?code=zhaobgg', '招标公告'),
        ('http://www.dtgpc.gov.cn/portal/netzfcg/gglist.aspx?code=zbgg', '中标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('tr > td > a[href^="zfcg/zbgg.aspx"]',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    # page_extractor = MetaLinkExtractor(css=('#netpager > a:contains(下一页)',))

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pages = self.page_extractor.links(response)
        # if pages:
        #     yield scrapy.Request(pages[0].url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#divggxx') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#lb_createdat'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
