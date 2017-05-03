import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class huangshan_1Spider(scrapy.Spider):
    """
    @title: 黄山市公共资源交易中心
    @href: http://www.hszgj.cn/hsweb/Default.aspx
    """
    name = 'anhui/huangshan/1'
    alias = '安徽/黄山'
    allowed_domains = ['hszgj.cn']
    start_urls = [
        ('http://www.hszgj.cn/hsweb/jyxx/004001/004001003/', '招标公告/建设工程'),
        ('http://www.hszgj.cn/hsweb/jyxx/004001/004001005/', '中标公告/建设工程'),
        ('http://www.hszgj.cn/hsweb/jyxx/004002/004002003/', '招标公告/政府采购'),
        ('http://www.hszgj.cn/hsweb/jyxx/004002/004002006/', '中标公告/政府采购'),
        ('http://www.hszgj.cn/hsweb/jyxx/004001/004001007/004001007001/', '招标公告/建设工程/小型'),
        ('http://www.hszgj.cn/hsweb/jyxx/004001/004001007/004001007003/', '中标公告/建设工程/小型'),
    ]

    link_extractor = MetaLinkExtractor(css='div.content tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

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
        body = response.css('#TDContent')
        prefix1 = '^\[\w{2,5}\]'
        prefix2 = '^<Font .+</Font>'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix1, '', title)
        title = re.sub(prefix2, '', title)
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
