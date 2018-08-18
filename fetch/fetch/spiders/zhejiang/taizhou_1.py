import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class ZhejiangTaizhou1Spider(scrapy.Spider):
    """
    @title: 台州市公共资源交易网
    @href: http://www.tzztb.com/tzcms/
    """
    name = 'zhejiang/taizhou/1'
    alias = '浙江/台州'
    allowed_domains = ['tzztb.com']
    start_urls = [
        ('http://www.tzztb.com/tzcms/gcjyzhaobgg/index.htm', '招标公告/建设工程'),
        ('http://www.tzztb.com/tzcms/gcjyzbgg/index.htm', '中标公告/建设工程'),
        ('http://www.tzztb.com/tzcms/zfcgcggg/index.htm', '招标公告/政府采购'),
        ('http://www.tzztb.com/tzcms/zfcgzbhxgs/index.htm', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='div.Right-list dl > dt a[target=_blank]',
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
        body = response.css('div.Main-p') or response.css('div.content-Border')
        prefix = '^\[\w{1,5}\]'

        day = FieldExtractor.date(data.get('day'), response.css('div.content-Border > em'))
        title = data.get('title') or FieldExtractor.text(response.css('div.content-Border > font.F-Sizee')) \
            or data.get('text')
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
