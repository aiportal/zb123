import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date, timedelta
import re


class liaoning_1Spider(scrapy.Spider):
    """
    @title: 辽宁省公共资源交易网
    @href: http://218.60.147.236/lnggzy/default.aspx
    """
    name = 'liaoning/1'
    alias = '辽宁'
    allowed_domains = ['218.60.147.236']
    start_base = 'http://218.60.147.236/lnggzy/showinfo/Morejyxx.aspx?'
    start_urls = [
        (start_base + 'num1=001&num2=001001&jyly=005', '招标公告/政府采购'),
        (start_base + 'num1=001&num2=001004&jyly=005', '中标公告/政府采购'),
        # (start_base + 'num1=001&num2=001002&jyly=005', '更正公告/政府采购'),
        (start_base + 'num1=002&num2=002001&jyly=005', '招标公告/建设工程'),
        (start_base + 'num1=002&num2=002004&jyly=005', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td a.ewb-list-name',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()',
                                                    'digest': '../../p//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        if re.match('^\s*<script .+</script>\s*', response.text):
            href = SpiderTool.re_text("location='(.+)'", response.text)
            url = urljoin(response.url, href)
            return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        data = response.meta['data']
        body = response.css('#zfcg_zbgs1_TDContent') or response.css('#jsgc_zbgs1_TDContent') \
            or response.css('#zfcg_zbgg1_TDContent, #zfcg_zbgg1_spnAttach') \
            or response.css('#jsgc_zbgg1_TDContent, #jsgc_zbgg1_spnAttach')
        pid = '\([A-Za-z0-9-]{10,18}\)'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(pid, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
