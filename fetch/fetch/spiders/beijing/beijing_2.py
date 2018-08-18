import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class beijing_2Spider(scrapy.Spider):
    """
    @title: 北京财政局-政府采购
    @href: http://www.bjcz.gov.cn/zfcgcs/index.htm
    """
    name = 'beijing/2'
    alias = '北京'
    allowed_domains = ['bjcz.gov.cn']
    start_urls = [
        ('http://www.bjcz.gov.cn/zfcgcs/bjszfcgggcs/zfcgcs/index.htm', '招标公告/政府采购/市级'),
        ('http://www.bjcz.gov.cn/zfcgcs/bjszfcgggcs/zbcjggcs/index.htm', '中标公告/政府采购/市级'),
        ('http://www.bjcz.gov.cn/zfcgcs/qzfcgggcs/qzbggcs/index.htm', '招标公告/政府采购/区级'),
        ('http://www.bjcz.gov.cn/zfcgcs/qzfcgggcs/qzbcjggcs/index.htm', '中标公告/政府采购/区级'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        re_nodes = '<d>\s*<t>(.+?)</t>\s*</d>'
        lns = re.findall(re_nodes, response.text, re.I | re.S)
        for ln in lns:
            href = SpiderTool.re_text(r' href="([^"]+)" target="_blank"', ln)
            data['text'] = SpiderTool.re_text(r'>(.+)</a>', ln)
            data['day'] = SpiderTool.re_text(r'\]\]>\s*(.+)\s*$', ln)
            url = urljoin(response.url, href)
            yield scrapy.Request(url, meta={'data': data}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#zoom')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
