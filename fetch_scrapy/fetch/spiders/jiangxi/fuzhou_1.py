import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re
from datetime import date


class fuzhou_1Spider(scrapy.Spider):
    """
    @title: 抚州公共资源交易网
    @href: http://www.fzztb.gov.cn/
    """
    name = 'jiangxi/fuzhou/1'
    alias = '江西/抚州'
    allowed_domains = ['fzztb.gov.cn']
    start_urls = [
        ('http://www.fzztb.gov.cn/zfcg/zbgg/', '招标公告/政府采购'),
        ('http://www.fzztb.gov.cn/zfcg/zbgs/', '中标公告/政府采购'),
        ('http://www.fzztb.gov.cn/jsgc/zbgg/', '招标公告/建设工程'),
        ('http://www.fzztb.gov.cn/jsgc/zbgs/', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='a[href^="./"][target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        data = response.meta['data']
        body = response.css('div.TRS_Editor') or response.css('#Zoom2')
        simple_day = '\[(\d{1,2})/(\d{1,2})\]'
        pid = '[(（]\w{2,5}编号[：:A-Z0-9-]{5,20}[）)]'

        if re.match(simple_day, data.get('day', '')):
            m, d = SpiderTool.re_nums(simple_day, data.get('day', ''))
            day = date(date.today().year, m, d)
            if day > date.today():
                day = date(date.today().year - 1, m, d)
        else:
            day = FieldExtractor.date(data.get('day', '').replace('/', '-'))

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
