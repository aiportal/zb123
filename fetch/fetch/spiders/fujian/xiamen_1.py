import scrapy
from fetch.extractors import NodesExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from datetime import date
import re


class FujianSpider(scrapy.Spider):
    """
    @title: 厦门政府采购网
    @href: http://www.xmzfcg.gov.cn/
    """
    name = 'fujian/xiamen/1'
    alias = '福建/厦门'
    allowed_domains = ['xmzfcg.gov.cn']
    start_urls = [
        ('http://www.xmzfcg.gov.cn/stockfile/preStockfileAction.do?cmd=prestockfile_index', '预公告'),
        ('http://www.xmzfcg.gov.cn/stockfile/stockfileAction.do?cmd=stockfile_index', '招标公告'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 2.0}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = NodesExtractor(css=('td > a[href^="javascript:ShowView"]',),
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

    def parse(self, response):
        nodes = self.link_extractor.extract_nodes(response)
        for node in nodes:
            href = SpiderTool.re_text("ShowView\('(.+)'\)", node['href'])
            url = 'http://www.xmzfcg.gov.cn/stockfile/' + href
            node.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': node}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('form > table') or response.css('body')
        if not body:
            url = 'http://www.xmzfcg.gov.cn' + SpiderTool.re_text('\.location\s*=\s*"(.+)";', response.text)
            if url:
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        day = FieldExtractor.date(data.get('day'), str(date.today()))
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
        return [g]
