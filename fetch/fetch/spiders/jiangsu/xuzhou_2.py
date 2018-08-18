import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class JiangsuXuzhouBuildSpider(scrapy.Spider):
    """
    @title: 徐州建设工程交易网
    @href: http://www.xzcet.com/xzwebnew/
    """
    name = 'jiangsu/xuzhou/2'
    alias = '江苏/徐州'
    allowed_domains = ['xzcet.com']
    start_urls = [
        ('http://www.xzcet.com/xzwebnew/ztbpages/MoreinfoZbgg.aspx?categoryNum=046001', '招标公告/建设工程', 0),
        ('http://www.xzcet.com/xzwebnew/ztbpages/MoreinfoZbrgg.aspx?categoryNum=046002', '中标公告/建设工程', 1),
    ]
    custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for url, subject, seq in self.start_urls:
            data = dict(subject=subject, seq=seq)
            yield scrapy.Request(url, meta={'data': data, 'cookiejar': seq}, dont_filter=True)

    link_extractors = [
        MetaLinkExtractor(css='#MoreinfoListJyxx1_DataGrid1 tr > td > a',
                          attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'}),
        MetaLinkExtractor(css='#moreinfoListZB1_DataGrid1 tr > td > a',
                          attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'}),
    ]
    # page_extractors = [
    #      NodeValueExtractor(css='#MoreinfoListJyxx1_Pager a > img[src$="nextn.gif"]', value_xpath='../@href'),
    #      NodeValueExtractor(css='#moreinfoListZB1_moreinfo a:contains(下一页)', value_xpath='./@href'),
    # ]

    def parse(self, response):
        seq = int(response.meta['data']['seq'])

        links = self.link_extractors[seq].links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractors[seq].extract_value(response) or ''
        # target, argument = SpiderTool.re_text("__doPostBack\('(.+)','(\d*)'\)", pager)
        # if target:
        #     form = {
        #         '__EVENTTARGET': target,
        #         '__EVENTARGUMENT': argument,
        #     }
        #     yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.xpath('//*[@id="TDContent" or @id="trAttach"]') or response.xpath('//*[@id="tblInfo"]')

        day = FieldExtractor.date(data.get('day'), response.xpath('//*[@id="tdTitle"]'))
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
