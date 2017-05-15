import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from datetime import date
import re


class LuZhouSpider(scrapy.Spider):
    """
    @title: 泸州市公共资源交易网
    @href: http://ggzy.luzhou.gov.cn/
    """
    name = 'sichuan/luzhou'
    alias = '四川/泸州'
    start_urls = [
        ('http://ggzy.luzhou.gov.cn/ceinwz/WebInfo_List.aspx?jsgc=0100000000&FromUrl=jsgc', '招标公告/建设工程'),
        ('http://ggzy.luzhou.gov.cn/ceinwz/WebInfo_List.aspx?jsgc=0000000100&FromUrl=jsgc', '中标公告/建设工程'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('#ctl00_ContentPlaceHolder1_myGV tr > td > a[href^=Hyzq]',),
                                       attrs_xpath={'text': './/text()', 'pid': '../../td[1]//text()'})
    # page_extractor = NodeValueExtractor(css=('tr.myGVPagerCss a:contains(下一页)',), value_xpath='./@href')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response) or ''
        # target, arg = SpiderTool.re_text("__doPostBack\('(.+)','(.*)'\)", pager)
        # if target:
        #     form = {
        #         '_EVENTTARGET': target,
        #         '__EVENTARGUMENT': arg,
        #     }
        #     yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#lblContent iframe') or response.css('#lblContent') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#lblWriteDate'),
                                  response.css('td:contains(发布时间) ~ td'), date.today())
        title = data.get('title') or data.get('text')
        title = re.sub('^\[.+\]', '', title)
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
