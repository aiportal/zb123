import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class ShanghaiMinxing1Spider(scrapy.Spider):
    """
    @title: 上海市闽行区公共资源交易网
    @href: http://ztb.shmh.gov.cn/
    """
    name = 'shanghai/minxing/1'
    alias = '上海/闽行'
    allowed_domains = ['shmh.gov.cn']
    start_urls = [
        ('http://ztb.shmh.gov.cn/mhztb_site/html/shmhztb_subject/{}/List/list_0.htm'.format(k), v)
        for k, v in [
            ('shmhztb_subject_jsgc_zbxx', '招标公告/建设工程'),
            ('shmhztb_subject_jsgc_zgbxx', '中标公告/建设工程'),
            ('shmhztb_subject_zfcg_cggg', '招标公告/政府采购'),
            ('shmhztb_subject_zfcg_jggg', '中标公告/政府采购'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='div.list_right ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('td.f12H > *')
        prefix = '^\w{2,10}信息—{1,2}'

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
