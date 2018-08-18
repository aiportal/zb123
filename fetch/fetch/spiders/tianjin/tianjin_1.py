import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class tianjin_1Spider(scrapy.Spider):
    """
    @title: 天津市政府采购中心
    @href: http://www.tjgpc.gov.cn/
    """
    name = 'tianjin/1'
    alias = '天津'
    allowed_domains = ['tjgpc.gov.cn']
    start_urls = [
        ('http://www.tjgpc.gov.cn/webInfo/getWebInfoListForwebInfoClass.do?fkWebInfoclassId={}'.format(k,), v)
        for k, v in [
            ('W005_001', '预公告/政府采购'),
            ('W001_001', '招标公告/政府采购'),
            ('W004_004', '更正公告/政府采购'),
            ('W004_001', '中标公告/政府采购'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='div.cur tr > td > a.project_title',
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
        body = response.css('td.xx')
        pid = '（\w{2,5}编号：[A-Z0-9-]+）'
        ignore = '^我中心本周无\w+信息发布$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        if re.match(ignore, title):
            return []
        title = re.sub(pid, '', title)
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
