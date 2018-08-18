import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class PanZhiHuaSpider(scrapy.Spider):
    """
    @title: 攀枝花市人民政府政务服务中心
    @href: http://www.pzhjs.com/
    """
    name = 'sichuan/pan_zhi_hua'
    alias = '四川/攀枝花'
    allowed_domains = ['pzhjs.com']
    start_urls = [
        ('http://www.pzhjs.com/JyWeb/XXGK/JYXTXXListGetXX?PageIndex=1&PageSize=15&{}'.format(k), v)
        for k, v in [
            ('SubType=1&SubType2=1010', '招标公告/建设工程'),
            ('SubType=1&SubType2=1030', '中标公告/建设工程'),
            # ('SubType=1&SubType2=1020', '更正公告/建设工程'),
            ('SubType=2&SubType2=2010', '招标公告/政府采购'),
            # ('SubType=2&SubType2=2020', '更正公告/政府采购'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('div.con tr > td > a',),
                                       attrs_xpath={'title': './span/@title', 'text': './/text()',
                                                    'day': '../../td[last()]//text()'})
    # page_extractor = MetaLinkExtractor(css=('#divPager a:contains(下一页)',),)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pages = self.page_extractor.links(response)
        # if pages:
        #     yield scrapy.Request(pages[0].url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#divJYXXCenter') or response.css('div.main_con') or response.css('div.main_wrap')

        day = FieldExtractor.date(data.get('day'), response.css('div.details_bar'))
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
