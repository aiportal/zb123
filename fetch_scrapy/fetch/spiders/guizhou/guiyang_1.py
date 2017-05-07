import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class guiyang_1Spider(scrapy.Spider):
    """
    @title: 贵阳市公共资源交易中心
    @href: http://www.gyggzy.cn/default.htm
    """
    name = 'guizhou/guiyang/1'
    alias = '贵州/贵阳'
    allowed_domains = ['gyggzy.cn']
    start_urls = [
        ('http://www.gyggzy.cn/catelist.aspx?cateid=ed21d176-a048-4a4d-aae0-2912015b8ceb&catename=招标公告',
         '招标公告/政府采购', 0),
        ('http://www.gyggzy.cn/catelist.aspx?cateid=bc143ae7-6e9f-431f-a2a6-7f9e25882799&catename=结果公示',
         '中标公告/政府采购', 0),
        ('http://www.gcjs.gyggzy.cn/gytendernotice/index.htm', '招标公告/建设工程', 1),
        ('http://www.gcjs.gyggzy.cn/gysuccpub/index.htm', '中标公告/建设工程', 1),
    ]

    link_extractors = [
        MetaLinkExtractor(css='div.sub-cont ul > li > a', attrs_xpath={'text': './/text()', 'day': '../code//text()'}),
        MetaLinkExtractor(css='div.list div.c1-bline a', attrs_xpath={'text': './/text()',
                                                                      'day': '../../div[@class="f-right"]//text()'}),
    ]

    def start_requests(self):
        for url, subject, extractor in self.start_urls:
            data = dict(subject=subject, extractor=extractor)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        extractor = self.link_extractors[response.meta['data']['extractor']]
        links = extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.gg') or response.css('div.news_content')

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
        return [g]
