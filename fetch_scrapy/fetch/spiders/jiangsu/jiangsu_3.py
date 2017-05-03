import scrapy
from fetch.extractors import NodesExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class Jiangsu3Spider(scrapy.Spider):
    """
    @title: 江苏建设工程招标网
    @href: http://www.jszb.com.cn/jszb/
    """
    name = 'jiangsu/3'
    alias = '江苏'
    allowed_domains = ['jszb.com.cn']
    start_urls = [
        ('http://www.jszb.com.cn/jszb/YW_info/ZhaoBiaoGG/MoreInfo_ZBGG.aspx', '招标公告'),
        ('http://www.jszb.com.cn/jszb/YW_info/ZhongBiaoGS/MoreInfo_ZBGS.aspx', '中标公告'),
    ]
    custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for i, (url, subject) in enumerate(self.start_urls):
            data = dict(subject=subject)
            meta = {'data': data, 'cookiejar': i}
            yield scrapy.Request(url, meta=meta, dont_filter=True)

    link_extractor = NodesExtractor(css='#MoreInfoList1_DataGrid1 tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                                 'industry': '../../td[last()-1]//text()'})
    page_extractor = NodeValueExtractor(css='#MoreInfoList1_Pager tr > td > a > img[src$="nextn.gif"]',
                                        value_xpath='../@href')

    def parse(self, response):
        links = self.link_extractor.extract_nodes(response)
        for lnk in links:
            href = SpiderTool.re_text('window\.open\("(.+)",".*",".+"\)', lnk.get('onclick', ''))
            url = urljoin(response.url, href)
            lnk.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': lnk}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        arg, num = SpiderTool.re_text("__doPostBack\('(.+)','(\d+)'\)", pager)
        if arg and num:
            form = {
                '__EVENTTARGET': arg,
                '__EVENTARGUMENT': num
            }
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#trzygg, #dlstAttachFile') or response.css('#Table1') or response.css('#tdContainer')
        prefix = '^\[(.+)\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        tag = SpiderTool.re_text(prefix, title)
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, tag])
        g.set(subject=[data.get('subject'), data.get('industry')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
