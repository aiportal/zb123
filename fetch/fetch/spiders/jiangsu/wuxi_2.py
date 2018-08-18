import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class JiangsuWuxi2Spider(scrapy.Spider):
    """
    @title: 无锡市公共资源交易中心
    @href: http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/index.shtml
    """
    name = 'jiangsu/wuxi/2'
    alias = '江苏/无锡'
    allowed_domains = ['wuxi.gov.cn']
    start_urls = [
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/jsgc/zbgg/gcl/index.shtml', '招标公告/建设工程/工程类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/jsgc/zbgg/fgcl/index.shtml', '招标公告/建设工程/非工程类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cghwgg1/cghwgg/index.shtml', '招标公告/政府采购/货物类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cghwgg1/cghwzbgg/index.shtml', '中标公告/政府采购/货物类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cghwgg1/cghwgzgg/index.shtml', '更正公告/政府采购/货物类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cgfwgg2/cgfwgg/index.shtml', '招标公告/政府采购/服务类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cgfwgg2/cghwzbgg1/index.shtml', '中标公告/政府采购/服务类'),
        ('http://xzfw.wuxi.gov.cn/ztzl/wxsggzyjyzx/zfcg/cgfwgg2/cgfwgzgg/index.shtml', '更正公告/政府采购/服务类'),
    ]

    link_extractor = MetaLinkExtractor(css='div.box04_con ul > li > a',
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
        body = response.css('#Zoom')
        prefix = '^\[[A-Z0-9-]+\]'
        suffix = '[A-Z0-9-]+$'

        day = FieldExtractor.date(data.get('day'), response.css('p.explain'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
