import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class ZhuhaiSpider(scrapy.Spider):
    """
    @title: 珠海市公共资源交易中心
    @href: http://ggzy.zhuhai.gov.cn/
    """
    name = 'guangdong/zhuhai'
    alias = '广东/珠海'
    allowed_domains = ['zhuhai.gov.cn']
    start_urls = [
        ('http://ggzy.zhuhai.gov.cn//cggg/index.htm', '招标公告'),
        ('http://ggzy.zhuhai.gov.cn//zczbgg/index.htm', '中标公告'),
        ('http://ggzy.zhuhai.gov.cn//gzgg/index.htm', '更正公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('ul.news > li > a:not([href$="/GPC"])',),
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    # page_extractor = NodeValueExtractor(css=('div.page a:contains(下一页)',), value_xpath='./@href')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # url = self.page_extractor.extract_value(response)
        # if url:
        #     yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.main2') or response.css('body')

        day = FieldExtractor.date(data.get('day'), body)
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
