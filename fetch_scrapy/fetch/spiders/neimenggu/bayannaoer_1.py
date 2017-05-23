import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class bayannaoer_1Spider(scrapy.Spider):
    """
    @title: 巴彦淖尔市政务服务中心
    @href: http://zwzx.bynr.gov.cn/sites/wy/index.jsp
    """
    name = 'neimenggu/bayannaoer/1'
    alias = '内蒙古/巴彦淖尔'
    allowed_domains = ['bynr.gov.cn']
    start_urls = [
        ('http://zwzx.bynr.gov.cn/sites/wy/list_key.jsp?ColumnID=57&SiteID=wy', '招标公告/政府采购'),
        ('http://zwzx.bynr.gov.cn/sites/wy/list_key.jsp?ColumnID=58&SiteID=wy', '中标公告/政府采购'),
        ('http://zwzx.bynr.gov.cn/sites/wy/list_key.jsp?ColumnID=52&SiteID=wy', '招标公告/建设工程'),
        ('http://zwzx.bynr.gov.cn/sites/wy/list_key.jsp?ColumnID=53&SiteID=wy', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.lis_right_nr ul > li > a[target=_blank]',
                                       attrs_xpath={'text': './span[1]//text()', 'day': './span[2]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('dl.del_rn')

        day = FieldExtractor.date(data.get('day') or response.css('dl.del_sj'))
        title = data.get('title') or data.get('text')
        if title.endswith('...'):
            title1 = FieldExtractor.text(response.css('dl.del_xb'))
            if len(title)-3 < len(title1) < 200:
                title = title1 or title
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
