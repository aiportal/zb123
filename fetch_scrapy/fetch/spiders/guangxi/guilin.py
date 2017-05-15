import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class GuilinSpider(scrapy.Spider):
    name = 'guangxi/guilin'
    alias = '广西/桂林'
    allowed_domains = ['guilin.cn']
    start_urls = [
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001001/001001001/', '招标公告/工程建设'),
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001001/001001002/', '更正公告/工程建设'),
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001001/001001006/', '中标公告/工程建设'),
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001004/001004001/', '招标公告/政府采购'),
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001004/001004006/', '更正公告/政府采购'),
        ('http://ggzy.guilin.cn/gxglzbw/jyxx/001004/001004002/', '中标公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('div.ewb-right ul > li a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../span//text()'})
    # page_extractor = NodeValueExtractor(css=('#Paging td:contains(下页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response) or ''
        # href = SpiderTool.re_text("\.href='(.+)'", pager)
        # if href:
        #     url = urljoin(response.url, href)
        #     yield scrapy.Request(url, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('tblInfo') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle > .word-info'), body)
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('#tdTitle > .word-title'))
        title = re.sub('^[.+]', '', title)
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
