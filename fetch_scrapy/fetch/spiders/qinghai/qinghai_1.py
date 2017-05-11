import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class qinghai_1Spider(scrapy.Spider):
    """
    @title: 青海省政府采购网
    @href: http://www.ccgp-qinghai.gov.cn/
    """
    name = 'qinghai/1'
    alias = '青海'
    allowed_domains = ['ccgp-qinghai.gov.cn']
    start_urls = [
        ('http://www.ccgp-qinghai.gov.cn/jilin/zbxxController.form?declarationType={}&pageNo=0&type=0'.format(k), v)
        for k, v in [
            ('GKZBGG', '招标公告/政府采购/公开招标'),
            ('XJZBGG', '预公告/政府采购/询价采购'),
            ('W', '中标公告/政府采购'),
            ('C', '变更公告/政府采购'),
            ('F', '废标公告/政府采购'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='div.m_list_3 ul > li a[target=_blank]',
                                       attrs_xpath={'text': './/text()',
                                                    'day': '../../div[@class="news_date"]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            href = SpiderTool.re_text('htmlURL=(.+)$', lnk.url)
            url = urljoin(response.url, '/' + href)
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('body')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
