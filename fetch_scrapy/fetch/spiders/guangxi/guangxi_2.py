import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class Guangxi2Spider(scrapy.Spider):
    name = 'guangxi/2'
    alias = '广西'
    allowed_domains = ['gxzfcg.gov.cn']
    start_urls = [
        ('http://www.gxzfcg.gov.cn/CmsNewsController/getCmsNewsList/channelCode-{}'
         '/param_bulletin/20/page_1.html'.format(k), v)
        for k, v in [
            ('shengji_zbwjygg', '预公告/省级'),
            ('shengji_cggg', '招标公告/省级'),
            ('shengji_zbgg', '中标公告/省级'),
            ('shengji_gzgg', '更正公告/省级'),

            ('sxjcg_zbwjygs', '预公告/市县'),
            ('sxjcg_cggg', '招标公告/市县'),
            ('sxjcg_zbgg', '中标公告/市县'),
            ('sxjcg_zbgg', '更正公告/市县'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('div.infoLink > ul > li > a',),
                                       attrs_xpath={'text': './text()', 'area': './span//text()',
                                                    'day': '../span[@class="date"]//text()'})
    page_extractor = NodeValueExtractor(css=('#QuotaList_paginate > span:nth-child(1)',), value_xpath='.//text()')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for link in links:
            link.meta.update(**response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page, count = SpiderTool.re_nums('页次：(\d+)/(\d+)页', pager)
        page += 1
        if page < count:
            url = re.sub('page_\d+\.html$', 'page_{}.html'.format(page), response.url)
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'), response.css('span.publishTime'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.reportTitle > h1'))
        contents = response.css('div.frameReport > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area', '').strip('[]')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.frameReport')))
        return [g]
