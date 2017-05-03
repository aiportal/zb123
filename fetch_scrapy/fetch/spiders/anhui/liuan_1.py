import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class liuan_1Spider(scrapy.Spider):
    """
    @title: 六安市公共资源交易网
    @href: http://www.laztb.gov.cn/lazbb/default.aspx
    """
    name = 'anhui/liuan/1'
    alias = '安徽/六安'
    allowed_domains = ['laztb.gov.cn']
    start_urls = [
        ('http://www.laztb.gov.cn/lazbb/jyxx/003001/003001001/', '招标公告/建设工程'),
        ('http://www.laztb.gov.cn/lazbb/jyxx/003001/003001003/', '中标公告/建设工程'),
        ('http://www.laztb.gov.cn/lazbb/jyxx/003002/003002001/', '招标公告/政府采购'),
        ('http://www.laztb.gov.cn/lazbb/jyxx/003002/003002004/', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='table.tab3 tr > td a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('.infodetail')
        suffix = '（\w{2,5}：[A-Z0-9-]号）$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(suffix, '', title)
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
