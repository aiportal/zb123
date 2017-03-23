import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class ZhoushanSpider(scrapy.Spider):
    name = 'jiangsu/zhoushan'
    alias = '江苏/舟山'
    allowed_domains = ['zszfcg.gov.cn']
    start_urls = [
        ('http://www.zszfcg.gov.cn/news/94.html', '招标公告/市级'),
        ('http://www.zszfcg.gov.cn/news/96.html', '中标公告/市级'),
        ('http://www.zszfcg.gov.cn/news/99.html', '招标公告/县级'),
        ('http://www.zszfcg.gov.cn/news/101.html', '中标公告/县级'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('ul.weblist > li a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../h2//text()'})
    page_extractor = MetaLinkExtractor(css=('div.page a:contains(下一页)',))

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        links = SpiderTool.url_filter(links, key=lambda x: x.url)
        for link in links:
            link.meta.update(**response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        pager = [x.url for x in self.page_extractor.extract_links(response)]
        if pager:
            yield scrapy.Request(pager[0], meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'), response.css('div.show_note'))
        title = data['text']    # or response.css('div.show_tit').extract()
        contents = response.css('div.show_txt > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.show_txt')))
        return [g]

