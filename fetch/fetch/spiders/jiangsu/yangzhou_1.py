import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class yangzhou_1Spider(scrapy.Spider):
    """
    @title: 扬州市公共资源交易中心
    @href: http://ggzyjyzx.yangzhou.gov.cn/
    """
    name = 'jiangsu/yangzhou/1'
    alias = '江苏/扬州'
    allowed_domains = ['yangzhou.gov.cn']
    start_urls = [
        ('http://www.yangzhou.gov.cn/qtyy/ggzyjyzx/right_list/{}'.format(k), v)
        for k, v in [
            ('right_list_jsgc.jsp?categorynum=003007', '招标公告/房建市政'),
            ('right_list_jsgc.jsp?categorynum=003008', '中标公告/房建市政'),
            ('right_list_jsgc.jsp?categorynum=003016', '招标公告/房建市政'),
            ('right_list_jsgc.jsp?categorynum=003013', '中标公告/房建市政'),
            ('right_list_zfcg.jsp?categorynum=002001', '招标公告/政府采购'),
            ('right_list_zfcg.jsp?categorynum=002002', '中标公告/政府采购'),
            ('right_list_cms.jsp?channel_id=bbde037ed4ae474684c1519b389169fd', '招标公告/交通工程'),
            ('right_list_cms.jsp?channel_id=5d23ee0536454d91bc26379dbd73eea5', '中标公告/交通工程'),
            ('right_list_slgc_zbgg.jsp', '招标公告/水利工程'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='ul.item > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content') or response.css('div.contentShow')
        prefix = '\[\w{1,5}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
