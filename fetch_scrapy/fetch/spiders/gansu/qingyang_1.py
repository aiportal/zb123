import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class qingyang_1Spider(scrapy.Spider):
    """
    @title: 庆阳市公共资源交易中心
    @href: http://www.qyggzyjy.gov.cn/
    """
    name = 'gansu/qingyang/1'
    alias = '甘肃/庆阳'
    allowed_domains = ['qyggzyjy.gov.cn']
    start_urls = [
        ('http://www.qyggzyjy.gov.cn/html/gonggaoZFCG/?Flag=3&subFlag=1', '招标公告/政府采购/公开招标'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoZFCG/?Flag=3&subFlag=1', '中标公告/政府采购/公开招标'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoZFCG/?Flag=1&subFlag=5', '招标公告/政府采购/询价公告'),

        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=1', '招标公告/建设工程/房建'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=2', '招标公告/建设工程/市政'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=3', '招标公告/建设工程/交通'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=4', '招标公告/建设工程/水利'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=5', '招标公告/建设工程/扶贫'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=6', '招标公告/建设工程/农业'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=1&subFlag=7', '招标公告/建设工程/土地'),

        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=1', '招标公告/建设工程/房建'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=2', '招标公告/建设工程/市政'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=3', '招标公告/建设工程/交通'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=4', '招标公告/建设工程/水利'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=5', '招标公告/建设工程/扶贫'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=6', '招标公告/建设工程/农业'),
        ('http://www.qyggzyjy.gov.cn/html/gonggaoJSGC/?Flag=4&subFlag=7', '招标公告/建设工程/土地'),
    ]

    link_extractor = MetaLinkExtractor(css='.psline a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../div[last()]//text()'})

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
        body = response.css('table.nywzh') or response.css('table.jsgctab')

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
