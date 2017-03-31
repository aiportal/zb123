import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class LeShanSpider(scrapy.Spider):
    """
    @title: 乐山市公共资源交易服务中心
    @href: http://lsggzy.com.cn/
    """
    name = 'sichuan/leshan'
    alias = '四川/乐山'
    allowed_domains = ['lsggzy.com.cn']
    start_urls = [
        ('http://lsggzy.com.cn/TPFront/jsgc_leshan/002001/', '招标公告/建设工程'),
        ('http://lsggzy.com.cn/TPFront/jsgc_leshan/002002/', '中标公告/建设工程'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('div.list tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('div.pagemargin td:contains(下页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        href = SpiderTool.re_text("ShowNewPage\('(.+)'\)", pager)
        if href:
            url = urljoin(response.url, href)
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent')  \
            # or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
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
