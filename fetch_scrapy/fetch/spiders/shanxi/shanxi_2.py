import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class Shanxi2Spider(scrapy.Spider):
    name = 'shanxi/2'
    alias = '山西'
    allowed_domains = ['ccgp-shanxi.gov.cn']
    start_urls = [
        ('http://www.ccgp-shanxi.gov.cn/view.php?nav=131', '预公告'),
        ('http://www.ccgp-shanxi.gov.cn/view.php?nav=100', '招标公告'),
        ('http://www.ccgp-shanxi.gov.cn/view.php?nav=104', '中标公告'),
        # ('http://www.ccgp-shanxi.gov.cn/view.php?nav=105', '更正公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#node_list tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'area': '../../td[2]//text()',
                                                    'day': '../../td[last()]//text()'})
    page_extractor = MetaLinkExtractor(css=('div.pager > a:contains(后一页)',))

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
        body = response.css('tr.bk5 table > tbody > tr:nth-child(3)') or response.css('tr.bk5 table') \
            or response.css('tr.bk5') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('tr.bk5 table > tbody > tr:nth-child(2)'))
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

