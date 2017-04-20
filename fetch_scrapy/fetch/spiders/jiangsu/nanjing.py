import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class NanjingSpider(scrapy.Spider):
    """
    @title: 四川省公共资源交易服务平台
    @href: http://www.scztb.gov.cn/
    """
    name = 'jiangsu/nanjing'
    alias = '江苏/南京'
    allowed_domains = ['njgp.gov.cn']
    start_urls = [
        ('http://www.njgp.gov.cn/cgxx/cggg/jzcgjg/', '招标公告/集中采购'),
        ('http://www.njgp.gov.cn/cgxx/cggg/bmjzcgjg/', '招标公告/部门集中采购'),
        ('http://www.njgp.gov.cn/cgxx/cggg/qjcgjg/', '招标公告/区级采购'),
        ('http://www.njgp.gov.cn/cgxx/cggg/shdljg/', '招标公告/社会代理'),
        ('http://www.njgp.gov.cn/cgxx/cggg/qtbx/', '招标公告/其他标讯'),
        ('http://www.njgp.gov.cn/cgxx/cgfsbg/', '更正公告/方式变更'),
        ('http://www.njgp.gov.cn/cgxx/cgcjjg/', '中标公告/成交结果'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('div.R_cont_detail > ul > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../text()'})

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        links = SpiderTool.url_filter(links, key=lambda x: x.url)
        for link in links:
            link.meta.update(subject=response.meta['data']['subject'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        pager = response.css('div.page_turn script:nth-child(2)').xpath('./text()').extract() + ['']
        pager = re.findall('createPageHTML\((\d+), (\d+)', pager[0].strip())
        if pager:
            page = int(pager[0][1]) + 1
            url = response.url
            url = '{0}/index_{1}.html'.format(url[:url.rfind('/')], page)
            yield scrapy.Request(url, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        prefix = '^【(.+)】'

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'), response.css('div.extra'))
        title = re.sub(prefix, '', data['text'])
        contents = response.css('div.article > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )

        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.article')))
        g.set(pid=(re.findall(prefix, data['text']) + [''])[0])
        return [g]
