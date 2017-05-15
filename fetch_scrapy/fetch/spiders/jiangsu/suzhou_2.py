import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class SuZhouSpider(scrapy.Spider):
    """
    @title: 苏州公共资源交易中心
    @href: http://www.szcetc.com.cn/
    """
    name = 'jiangsu/suzhou_2'
    alias = '江苏/苏州'
    allowed_domains = ['szcetc.com.cn', '218.4.168.194']
    start_urls = [
        ('http://www.szcetc.com.cn/Front/showinfo/jyzxmore.aspx?CategoryNum=002001001&Paging=1', '招标公告/建设工程'),
        # ('http://www.szcetc.com.cn/Front/showinfo/zbgsmore.aspx?CategoryNum=002001006&Paging=1', '中标公告/建设工程'),
        # 交通工程类招标信息会转向到 http://www.infobidding.com/
        # ('http://www.szcetc.com.cn/Front/showinfo/gcjs_more.aspx?CategoryNum=002002002&Paging=1', '招标公告/交通工程'),
        # ('http://www.szcetc.com.cn/Front/showinfo/gcjs_more.aspx?CategoryNum=002002004&Paging=1', '中标公告/交通工程'),
        # ('http://www.szcetc.com.cn/Front/showinfo/gcjs_more.aspx?CategoryNum=002003001&Paging=1', '招标公告/水利工程'),
        # ('http://www.szcetc.com.cn/Front/showinfo/gcjs_more.aspx?CategoryNum=002003005&Paging=1', '中标公告/水利工程'),
        ('http://www.szcetc.com.cn/Front/jyzx/002004/002004001/', '招标公告/政府采购'),
        ('http://www.szcetc.com.cn/Front/jyzx/002004/002004002/', '中标公告/政府采购'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.68, 'DEPTH_LIMIT': 3}

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#tdcontent tr > td > a, div.mr-content tr > td > a',),
                                       attrs_xpath={'text': './/text()',
                                                    'day': '../../td[last()]//text() | ../../td[last()-1]//text()'})
    # page_extractor = NodeValueExtractor(css=('div.pagemargin td:contains(下页)',), value_xpath='./@onclick')

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
        # 如果是转向操作，转到实际页面
        if re.match('^\<script\>.+\</script\>', response.text):
            script = FieldExtractor.text(response.css('script')) or ''
            url = SpiderTool.re_text("window.location='(.+)'", script)
            if url:
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]
        # 服务器防护，模拟点击
        if re.match('function JumpSelf\(\)', response.text):
            script = FieldExtractor.text(response.xpath('//script/text()')) or ''
            url = SpiderTool.re_text('self.location="(.+)";', script)
            if url:
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('#Table2') or response.css('#content')

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
        g.set(extends=data)
        return [g]
