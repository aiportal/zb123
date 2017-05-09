import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class hubei_1Spider(scrapy.Spider):
    """
    @title: 湖北省政府采购网
    @href: http://www.ccgp-hubei.gov.cn/
    """
    name = 'hubei/1'
    alias = '湖北'
    allowed_domains = ['ccgp-hubei.gov.cn']
    start_urls = [
        ('http://www.ccgp-hubei.gov.cn/pages/html/szbnotice.html', '招标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/pages/html/sjgnotice.html', '中标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/pages/html/sfbnotice.html', '废标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/pages/html/sgznotice.html', '更正公告/政府采购/省级'),
        # ('', '招标公告/政府采购/市级'),
        # ('', '中标公告/政府采购/市级'),
        # ('', '废标公告/政府采购/市级'),
        # ('', '更正公告/政府采购/市级'),
    ]

    link_extractor = MetaLinkExtractor(css='div.news_content ul > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        links = links[:15]
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        if response.css('#mainFrame'):
            src = response.css('#mainFrame').xpath('./@src').extract_first()
            url = urljoin(response.url, src)
            return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]
        data = response.meta['data']
        body = response.css('div.notic_show_content') or response.xpath('//div[@class="notic_show_content"]')

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
