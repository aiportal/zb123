import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class JiangsuLyg1Spider(scrapy.Spider):
    """
    @title: 连云港市公共资源交易中心
    @href: http://www.lygztb.gov.cn/TPFront/
    """
    name = 'jiangsu/lianyungang/1'
    alias = '江苏/连云港'
    allowed_domains = ['lygztb.gov.cn']
    start_urls = [
        ('http://www.lygztb.gov.cn/TPFront/ztb/jsgc/zbgg_more.aspx', '招标公告/建设工程'),
        ('http://www.lygztb.gov.cn/TPFront/ztb/jsgc/zhongbgg_more.aspx', '中标公告/建设工程'),
        ('http://www.lygztb.gov.cn/TPFront/xxgk/009002/009002001/', '招标公告/水利工程'),
        ('http://www.lygztb.gov.cn/TPFront/xxgk/009002/009002006/', '中标公告/水利工程'),
        ('http://www.lygztb.gov.cn/TPFront/xxgk/009003/009003001/', '招标公告/交通工程'),
        ('http://www.lygztb.gov.cn/TPFront/xxgk/009003/009003006/', '中标公告/交通工程'),
    ]

    link_extractor = MetaLinkExtractor(css='.ej-n tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#TDContent') or response.css('.infodetail') or \
            response.css('epointform') or response.css('#spnContent')

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
