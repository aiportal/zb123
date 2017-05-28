import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class anshun_1Spider(scrapy.Spider):
    """
    @title: 安顺市公共资源交易网
    @href: http://ggzy.anshun.gov.cn/
    """
    name = 'guizhou/anshun/1'
    alias = '贵州/安顺'
    allowed_domains = ['anshun.gov.cn']
    start_urls = [
        ('http://ggzy.anshun.gov.cn/list/4B.html?type=4B1', '招标公告/政府采购'),
        ('http://ggzy.anshun.gov.cn/list/4B.html?type=4B2', '中标公告/政府采购'),
        ('http://ggzy.anshun.gov.cn/list/4B.html?type=4B3', '废标公告/政府采购'),
        ('http://ggzy.anshun.gov.cn/list/4A.html?type=4A1', '招标公告/建设工程'),
        ('http://ggzy.anshun.gov.cn/list/4A.html?type=4A2', '中标公告/建设工程'),
        ('http://ggzy.anshun.gov.cn/list/4A.html?type=4A3', '废标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.02}

    link_extractor = MetaLinkExtractor(css='div.text_box ul > li a',
                                       attrs_xpath={'text': './/text()', 'day': '../../p.time//text()'})

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
        body = response.css('div.text_text')

        day = FieldExtractor.date(data.get('day'), response.css('div.text_title > div.small'))
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
