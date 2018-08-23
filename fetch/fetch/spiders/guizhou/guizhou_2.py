import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class guizhou_2Spider(scrapy.Spider):
    """
    @title: 贵州省公共资源交易中心
    @href: http://www.gzsggzyjyzx.cn/
    """
    name = 'guizhou/2'
    alias = '贵州'
    allowed_domains = ['gzsggzyjyzx.cn']
    # start_urls = ['http://www.gzsggzyjyzx.cn/ajax_trace']
    # start_params = [
    #     ('招标公告/政府采购', {'cls': '4B', 'type': '4B1', 'classif_no': 'All', 'rownum': '20'}),
    #     ('中标公告/政府采购', {'cls': '4B', 'type': '4B2', 'classif_no': 'All', 'rownum': '20'}),
    #     ('招标公告/建设工程', {'cls': '4A', 'type': '4A1', 'classif_no': 'All', 'rownum': '20'}),
    #     ('中标公告/建设工程', {'cls': '4A', 'type': '4A2', 'classif_no': 'All', 'rownum': '20'}),
    # ]
    start_urls = [
        ('http://www.gzsggzyjyzx.cn/jygkzsgg/index.jhtml', '招标公告/工程建设'),
        ('http://www.gzsggzyjyzx.cn/jygkycgg/index.jhtml', '废标公告/工程建设'),
        ('http://www.gzsggzyjyzx.cn/jygkcgxm/index.jhtml', '招标公告/政府采购'),
        ('http://www.gzsggzyjyzx.cn/jygkzbgg/index.jhtml', '废标公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#listbox li a',
                                       attrs_xpath={'text': './/text()', 'day': '../../div.content_right//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.detail_box')
        tail = '<font (.+)</font>$'
        symbol = '&[a-z]+;'

        day = FieldExtractor.date(data.get('date'), response.css('div.article_subtitle'))
        title = data.get('title') or data.get('text')
        title = re.sub(tail, '', title)
        title = re.sub(symbol, '', title)
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
