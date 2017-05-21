import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date


class zhuzhou_1Spider(scrapy.Spider):
    """
    @title: 株洲市公共资源交易中心
    @href: http://www.zzztb.net/zzweb/Default.aspx
    """
    name = 'hunan/zhuzhou/1'
    alias = '湖南/株洲'
    allowed_domains = ['zzztb.net']
    start_urls = [
        ('http://www.zzztb.net/zzweb/ZtbInfo/zbxx_ZBGG_List.aspx', '招标公告'),
        # ('http://www.zzztb.net/zzweb/ZtbInfo/zbxx_ZBGS_List.aspx', '中标公告'),
    ]

    link_extractor = MetaLinkExtractor(css='#tdcontent tr > td > a',
                                       attrs_xpath={'text': './/text()'})

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
        body = response.css('table[border="1"]')

        day = FieldExtractor.date(data.get('day') or str(date.today()))
        title = data.get('title') or data.get('text')
        contents = [body.extract_first()]
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
