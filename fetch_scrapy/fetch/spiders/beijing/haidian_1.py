import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class haidian_1Spider(scrapy.Spider):
    """
    @title: 北京市海淀区公共资源交易信息网
    @href: http://ggzyjy.bjhd.gov.cn/
    """
    name = 'beijing/haidian/1'
    alias = '北京/海淀'
    allowed_domains = ['bjhd.gov.cn']
    start_urls = [
        ('http://ggzyjy.bjhd.gov.cn//zfcgTender/index.htm', '招标公告/政府采购'),
        ('http://ggzyjy.bjhd.gov.cn//zfcgWinner/index.htm', '中标公告/政府采购'),
        ('http://ggzyjy.bjhd.gov.cn//zfcgBidbefore/index.htm', '预公告/政府采购'),
        ('http://ggzyjy.bjhd.gov.cn//zfcgInfoModify/index.htm', '更正公告/政府采购'),
        ('http://ggzyjy.bjhd.gov.cn//zfcgAbend/index.htm', '其他公告/废标公告'),
    ]

    link_extractor = MetaLinkExtractor(css='div.cont-main ul > li a',
                                       attrs_xpath={'text': './/text()', 'day': '../../div[last()]//text()'})

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
        body = response.css('div.xiangxi')
        prefix = '^\[[A-Z0-9-]+\]'

        day = FieldExtractor.date(data.get('day'))
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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
