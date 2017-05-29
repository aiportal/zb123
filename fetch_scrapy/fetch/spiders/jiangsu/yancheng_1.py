import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class yancheng_1Spider(scrapy.Spider):
    """
    @title: 盐城市公共资源交易网
    @href: http://www.ycsggzy.gov.cn/front/
    """
    name = 'jiangsu/yancheng/1'
    alias = '江苏/盐城'
    allowed_domains = ['ycsggzy.gov.cn']
    start_base = 'http://www.ycsggzy.gov.cn/front/showinfo/moreinfo_search.aspx'
    start_urls = [
        (start_base + '?categoryNum=009&type=001', '招标公告/工程建设'),
        (start_base + '?categoryNum=009&type=006', '中标公告/工程建设'),
        (start_base + '?categoryNum=011&type=004', '预公告/政府采购'),
        (start_base + '?categoryNum=011&type=001', '招标公告/政府采购'),
        (start_base + '?categoryNum=011&type=003', '中标公告/政府采购'),
        (start_base + '?categoryNum=010&type=001', '招标公告/货物服务'),
        (start_base + '?categoryNum=010&type=003', '中标公告/货物服务'),
        (start_base + '?categoryNum=010&type=005', '废标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data=dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#moreinfo_search_fl1_tdcontent tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('.infodetail')

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
