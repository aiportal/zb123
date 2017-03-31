import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class LiangShanSpider(scrapy.Spider):
    """
    @title: 凉山州人民政府政务服务中心
    @href: http://www.lszw.gov.cn/
    """
    name = 'sichuan/liangshan'
    alias = '四川/凉山'
    start_urls = [
        ('http://www.lszw.gov.cn/plus/list.php?tid=30', '招标公告/凉山州'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('ul.artlist > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    page_extractor = MetaLinkExtractor(css=('ul.pagelist a:contains(下一页)',),)

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
        body = response.css('div.c_content') or response.css('div.article_content')

        day = FieldExtractor.date(data.get('day'), response.css('div.son_title tc'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.title tc'))
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
