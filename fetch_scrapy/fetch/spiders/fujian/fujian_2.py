import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class fujian_2Spider(scrapy.Spider):
    """
    @title: 福建省公共资源交易中心
    @href: http://fjggzyjy.cn/
    """
    name = 'fujian/2'
    alias = '福建'
    allowed_domains = ['fjggzyjy.cn']
    start_urls = [
        ('http://fjggzyjy.cn/news/category/46/', '招标公告/建设工程/房建市政'),
        ('http://fjggzyjy.cn/news/category/50/', '中标公告/建设工程/房建市政'),
        ('http://fjggzyjy.cn/news/category/52/', '招标公告/建设工程/交通水利'),
        ('http://fjggzyjy.cn/news/category/56/', '中标公告/建设工程/交通水利'),
        ('http://fjggzyjy.cn/news/category/10/', '招标公告/政府采购'),
        ('http://fjggzyjy.cn/news/category/12/', '中标公告/政府采购'),
        ('http://fjggzyjy.cn/news/category/14/', '招标公告/政府采购/网上竞价'),
    ]

    link_extractor = MetaLinkExtractor(css='div.article-list-template a',
                                       attrs_xpath={'text': './span[@class="article-list-text"]/text()',
                                                    'day': './span[@class="article-list-date"]//text()',
                                                    'pid': './span[@class="article-list-number"]/text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.article-content')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        g.set(pid=data.get('pid'))
        return [g]
