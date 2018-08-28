import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shaanxi_1Spider(scrapy.Spider):
    """
    @title: 陕西省政府采购
    @href: http://www.ccgp-shaanxi.gov.cn/index.jsp
    """
    name = 'shaanxi/1'
    alias = '陕西'
    allowed_domains = ['ccgp-shaanxi.gov.cn']
    start_urls = [
        ('http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype=1', '预公告'),
        ('http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype=3', '招标公告'),
        ('http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype=4', '更正公告'),
        ('http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype=5', '中标公告'),
        ('http://www.ccgp-shaanxi.gov.cn/notice/noticeaframe.do?noticetype=6', '废标公告'),
    ]
    # custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.list-box tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                       'area': '../../td[2]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content-inner')

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
        g.set(area=[self.alias, data.get('area', '').strip('[]')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
