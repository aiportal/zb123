import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class anhui_2Spider(scrapy.Spider):
    """
    @title: 安徽省建设工程招标投标信息网
    @href: http://www.act.org.cn/
    """
    name = 'anhui/2'
    alias = '安徽'
    allowed_domains = ['act.org.cn']
    start_urls = [
        ('http://www.act.org.cn/news.asp?pid=169', '招标公告/建设工程'),
        ('http://www.act.org.cn/News.Asp?pid=171', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.sublist_list ul > li > a',
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
        body = response.css('div.subcont_cont > *:not(.print)')

        day = FieldExtractor.date(data.get('day'), response.css('div.subcont_title div.msg'))
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
