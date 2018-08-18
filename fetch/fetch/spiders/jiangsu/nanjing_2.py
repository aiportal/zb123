import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class JiangsuNanjing2Spider(scrapy.Spider):
    """
    @title: 南京市公共资源交易中心
    @href: http://ggzy.njzwfw.gov.cn/njggzy/
    """
    name = 'jiangsu/nanjing/2'
    alias = '江苏/南京'
    allowed_domains = ['njzwfw.gov.cn']
    start_urls = [
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001001/001001001', '招标公告/建设工程'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001001/001001003', '中标公告/建设工程'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001001/001001004/001001004001/', '招标公告/建设工程/小型'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001001/001001004/001001004002/', '中标公告/建设工程/小型'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001002/001002004/', '招标公告/交通航运'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001002/001002003/', '中标公告/交通航运'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001003/001003001/', '招标公告/水利'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001003/001003002/', '中标公告/水利'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001004/001004001/', '招标公告/铁路'),
        ('http://ggzy.njzwfw.gov.cn/njggzy/jsgc/001004/001004002/', '中标公告/铁路'),
        # ('http://ggzy.njzwfw.gov.cn/njggzy/zfcg/002001/002001004/', '招标公告/政府采购'),
        # ('http://ggzy.njzwfw.gov.cn/njggzy/zfcg/002002/002002001/', '中标公告/政府采购'),
        # ('http://ggzy.njzwfw.gov.cn/njggzy/zfcg/002002/002002002/', '更正公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='a[href^="/njggzy/infodetail"]',
                                       attrs_xpath={'text': './/text()', 'day': '../../../td[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        assert links

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#tblInfo')
        prefix = '^（(\w+)）'

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
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
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
