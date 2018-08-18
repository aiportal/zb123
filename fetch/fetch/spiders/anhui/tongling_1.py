import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class tongling_1Spider(scrapy.Spider):
    """
    @title: 铜陵市公共资源交易网
    @href: http://www.tlzbcg.com/tlsggzy/
    """
    name = 'anhui/tongling/1'
    alias = '安徽/铜陵'
    allowed_domains = ['tlzbcg.com']
    start_urls = [
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=006003', '预公告/建设工程'),
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=006001001', '招标公告/建设工程'),
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=006001004', '中标公告/建设工程'),
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=007003', '预公告/政府采购'),
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=007001001', '招标公告/政府采购'),
        ('http://www.tlzbcg.com/tlsggzy/ZtbInfo/zhaobiao.aspx?categorynum=007001004', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './text()', 'day': '../../td/span//text()'})

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
        body = response.css('#TDContent, #filedown')
        prefix = '^\w{2,8}：'

        day = FieldExtractor.date(response.css('td:contains(阅读次数)'), '20' + data.get('day'))
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
