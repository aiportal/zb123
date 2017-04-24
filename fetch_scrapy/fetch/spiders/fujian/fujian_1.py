import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class fujian_1Spider(scrapy.Spider):
    """
    @title: 福建省政府采购网
    @href: http://cz.fjzfcg.gov.cn/
    """
    name = 'fujian/1'
    alias = '福建'
    allowed_domains = ['fjzfcg.gov.cn']
    start_urls = [
        ('http://cz.fjzfcg.gov.cn/notice/noticelist/?notice_type=200000005', '预公告/资格预审'),
        ('http://cz.fjzfcg.gov.cn/notice/noticelist/?notice_type=200000001', '招标公告/采购公告'),
        ('http://cz.fjzfcg.gov.cn/notice/noticelist/?notice_type=200000002', '更正公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='.pag_box19 ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('.pag_box29')

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
