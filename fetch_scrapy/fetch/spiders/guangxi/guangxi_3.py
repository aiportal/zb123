import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class Guangxi3Spider(scrapy.Spider):
    name = 'guangxi/3'
    alias = '广西'
    allowed_domains = ['gxi.gov.cn']
    start_urls = [
        ('http://ztb.gxi.gov.cn/ztbgg/ztbtg/', '招标公告'),
        ('http://ztb.gxi.gov.cn/ztbgg/zbgs/', '中标公告'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 1.1}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#OutlineContent tr > td > span > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../font//text()'})
    page_extractor = NodeValueExtractor(css=('#OutlineContent ~ tr script',), value_xpath='./text()')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        count, page = SpiderTool.re_nums('createPageHTML\((\d+),(\d+),', pager)
        page += 1
        if page < count:
            url = response.url
            url = url[:url.rfind('/')] + '/index_{}.htm'.format(page)
            yield scrapy.Request(url, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.xpath('/html/body/table[2]//table//table//table[4]') \
            or response.xpath('/html/body/table[2]//table//table//table') or response.css('body')

        day = FieldExtractor.date(data.get('day'), body)
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('td.newtitle').xpath('./text()'))
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
