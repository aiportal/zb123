import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class JiangsuNeijiang1Spider(scrapy.Spider):
    """
    @title: 内江市公共资源交易服务中心
    @href: http://www.njztb.cn/
    """
    name = 'sichuan/neijiang/1'
    alias = '四川/内江'
    allowed_domains = ['njztb.cn']
    start_base_zfcg = 'http://zfcg.njztb.cn/ceinwz/WebInfo_List.aspx'
    start_urls = [
        ('http://ztb.njztb.cn/ceinwz/WebInfo_List.aspx?newsid=0&jsgc=0100000&showdate=1', '招标公告/建设工程'),
        (start_base_zfcg + '?zfcg=0100000&newsid=201&FromUrl=zfcg&showdate=1', '招标公告/政府采购'),
        (start_base_zfcg + '?zfcg=0000001&newsid=204&FromUrl=zfcg&showdate=1', '中标公告/政府采购'),
        (start_base_zfcg + '?zfcg=0010000&newsid=202&FromUrl=zfcg&showdate=1', '更正公告/政府采购'),
        (start_base_zfcg + '?newsid=10001,11001,12001,13001&showdate=1&FromUrl=zfcg', '招标公告/政府采购/区县')
    ]

    link_extractor = MetaLinkExtractor(css='table.myGVClass tr > td > a[id$=HLinkGcmc]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                                    'pid': '../../td[1]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    frame_extractor = NodeValueExtractor(css='iframe', value_xpath='./@src')

    def parse_frame(self, response):
        src = self.frame_extractor.extract_value(response)
        url = urljoin(response.url, src)
        yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('body')
        prefix = '^\[\w{1,5}\]'

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
        g.set(pid=data.get('pid'))
        return [g]
