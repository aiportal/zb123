import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class Jiangxi1Spider(scrapy.Spider):
    """
    @title: 江西省公共资源交易网
    @href: http://ggzy.jiangxi.gov.cn/jxzbw/
    """
    name = 'jiangxi/1'
    alias = '江西'
    allowed_domains = ['jiangxi.gov.cn']
    start_urls = [
        ('http://ggzy.jiangxi.gov.cn/jxzbw/jyxx/{1}/{0}/MoreInfo.aspx?CategoryNum={0}'.format(k, k[:6]), v)
        for k, v in [
            ('002001002', '招标公告/房建及市政'),
            ('002001005', '中标公告/房建及市政'),
            ('002002002', '招标公告/交通工程'),
            ('002002005', '中标公告/交通工程'),
            ('002003001', '招标公告/水利工程'),
            ('002003004', '中标公告/水利工程'),
            # ('002009001', '招标公告/铁路工程'),
            # ('002009004', '中标公告/铁路工程'),
            ('002004001', '招标公告/政府采购'),
            ('002004004', '中标公告/政府采购'),
            ('002010001', '招标公告/重点工程'),
            ('002010004', '中标公告/重点工程'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#MoreInfoList1_DataGrid1 tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('.infodetail')

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
