import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class Beijing2Spider(scrapy.Spider):
    name = 'beijing/2'
    alias = '北京'
    allowed_domains = ['www.bgpc.gov.cn']
    start_urls = [
        ('http://www.bgpc.gov.cn/news/news/nt_id/97', '预公告/需求公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/29', '招标公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/32', '中标公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/30', '更正公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/33', '其他公告/废标公告')
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('#newslist > ul > li > span > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../span[last()]//text()'})
    page_extractor = MetaLinkExtractor(css=('div.paginationControl a:contains(下一页)',))

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pages = self.page_extractor.links(response)
        if pages:
            yield scrapy.Request(pages[0].url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.news_content') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('div.news_time'), body)
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('h1.news_title'))
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
