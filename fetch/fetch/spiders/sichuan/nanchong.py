import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class NanchongSpider(scrapy.Spider):
    """
    @note: 南充市公共资源交易中心
    @see: http://ggzy.scnczw.gov.cn
    """
    name = 'sichuan/nanchong'
    alias = '四川/南充'
    start_urls = [
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072001/', '招标公告/工程建设'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072004/', '中标公告/工程建设'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072002/', '更正公告/工程建设'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072006/072006001/', '招标公告/工程建设/区县'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072006/072006004/', '中标公告/工程建设/区县'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_gcjs/072006/072006002/', '更正公告/工程建设/区县'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071002/', '招标公告/政府采购'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071005/', '中标公告/政府采购'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071003/', '更正公告/政府采购'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071008/071008001/', '招标公告/政府采购/区县'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071008/071008003/', '中标公告/政府采购/区县'),
        ('http://ggzy.scnczw.gov.cn/TPFront/front_zfcg/071008/071008002/', '更正公告/政府采购/区县'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('ul.list-ul > li > a',),
                                       attrs_xpath={'text': './span[1]//text()', 'day': './span[2]//text()'})
    # page_extractor = NodeValueExtractor(css=('div.pagemargin td:contains(下页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response) or ''
        # href = SpiderTool.re_text("\.href='(.+)'", pager) or SpiderTool.re_text("ShowNewPage\('(.+)'\)", pager)
        # if href:
        #     url = urljoin(response.url, href)
        #     yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('epointform') or response.css('#_Sheet1') \
            or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('#tdTitle > div:nth-child(1)'))
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
