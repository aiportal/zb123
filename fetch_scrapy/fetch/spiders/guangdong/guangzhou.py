import scrapy
from fetch.tools import SpiderTool
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.items import GatherItem
import re


class GuangzhouSpider(scrapy.Spider):
    name = 'guangdong/guangzhou'
    alias = '广东/广州'
    allowed_domains = ['gzggzy.cn']

    start_urls = [
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=503', '招标公告/房建市政'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=510', '招标公告/交通'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=515', '招标公告/电力'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=520', '招标公告/铁路'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=525', '招标公告/水利'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=543', '招标公告/园林'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=539', '招标公告/民航'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=530', '招标公告/其他'),
        ('http://www.gzggzy.cn/cms/wz/view/index/layout2/szlist.jsp?siteId=1&channelId=535', '招标公告/其他')
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('table.wsbs-table > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('div.pagination a:contains(下一页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for link in links:
            link.meta.update(response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        page = self.page_extractor.extract_value(response)
        page = re.findall('goPage\((\d+)\)', page or '')
        if page:
            url = SpiderTool.url_replace(response.url, page=page[0])
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'))
        contents = response.css('div.xx-text > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=data.get('title') or data.get('text'),
            contents=contents
        )

        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.xx-text')))
        return [g]
