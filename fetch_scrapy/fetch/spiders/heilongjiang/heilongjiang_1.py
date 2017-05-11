import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class heilongjiang_1Spider(scrapy.Spider):
    """
    @title: 黑龙江省政府采购网
    @href: http://www.hljcg.gov.cn/xwzs!index.action
    """
    name = 'heilongjiang/1'
    alias = '黑龙江'
    allowed_domains = ['hljcg.gov.cn']
    start_urls = [
        ('http://www.hljcg.gov.cn/xwzs!queryXwxxqx.action?lbbh=4', '招标公告/政府采购'),
        ('http://www.hljcg.gov.cn/xwzs!queryXwxxqx.action?lbbh=5', '中标公告/政府采购'),
    ]
    custom_settings = {'COOKIES_ENABLED': True}

    link_extractor = NodesExtractor(css='div.yahoo span.lbej a[onclick]',
                                    attrs_xpath={'text': './/text()', 'day': '../../span[last()-1]//text()'})

    def start_requests(self):
        # 先访问主页以获得Cookie
        url = 'http://www.hljcg.gov.cn/xwzs!index.action'
        yield scrapy.Request(url, dont_filter=True, callback=self.start_requests_real)

    def start_requests_real(self, response):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            href = SpiderTool.re_text("location.href='(.+)';", row['onclick'])
            url = urljoin(response.url, href)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.xxej > *:not(div.mtt)')

        day = FieldExtractor.date(data.get('day'), response.css('div.mtt'))
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
