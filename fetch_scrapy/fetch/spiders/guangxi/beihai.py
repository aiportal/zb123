import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class BeihaiSpider(scrapy.Spider):
    name = 'guangxi/beihai'
    alias = '广西/北海'
    allowed_domains = ['beihaizc.com.cn']
    start_urls = [
        ('http://www.beihaizc.com.cn/g_info_list_1.asp?id=12', '预公告'),
        ('http://www.beihaizc.com.cn/g_info_list_1.asp?id=4', '招标公告'),
        ('http://www.beihaizc.com.cn/g_info_list_1.asp?id=5', '中标公告'),
        ('http://www.beihaizc.com.cn/g_info_list_1.asp?id=14', '更正公告'),
        ('http://www.beihaizc.com.cn/g_info_list_1.asp?id=13', '其他公告/废标公告')
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('form ~ tr > td > table table tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    # page_extractor = MetaLinkExtractor(css=('form ~ tr > td > table > tbody > tr:nth-child(3) a:contains(下页)',))

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
        body = response.xpath('//img[@src="Images/fanhui.png"]/../../../tr[1]') or response.css('body')

        day = FieldExtractor.date(data.get('day'), body)
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
