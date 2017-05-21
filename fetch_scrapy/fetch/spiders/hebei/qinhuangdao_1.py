import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class qinhuangdao_1Spider(scrapy.Spider):
    """
    @title: 秦皇岛市公共资源交易网
    @href: http://www.qhdggzy.gov.cn/ggzyjyw/index.jsp
    """
    name = 'hebei/qinhuangdao/1'
    alias = '河北/秦皇岛'
    allowed_domains = ['qhdggzy.gov.cn']
    start_urls = [
        ('http://www.qhdggzy.gov.cn/ggzyjyw/article_purchaseBulletinList.do', '招标公告/政府采购'),
        ('http://www.qhdggzy.gov.cn/ggzyjyw/article_purchaseGuideList.do', '中标公告/政府采购'),
        ('http://www.qhdggzy.gov.cn/ggzyjyw/bulletin_bulletinList.do', '招标公告/建设工程'),
        ('http://www.qhdggzy.gov.cn/ggzyjyw/bidWinnerList_bidWinnerList.do', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.content2_r_3 ul > li a',
                                       attrs_xpath={'text': './/text()', 'day': '../../span[last()]//text()'})

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
        body = response.css('#bulletin_content') or response.css('#choiceContent') or response.css('#content_')

        day = FieldExtractor.date(data.get('day'), response.css('td.time'))
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
