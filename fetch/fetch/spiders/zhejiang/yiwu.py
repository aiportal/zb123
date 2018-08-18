import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class YiwuSpider(scrapy.Spider):
    name = 'zhejiang/yiwu'
    alias = '浙江/义乌'
    allow_domains = ['yw.gov.cn']
    start_urls = [
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/01/01/', '招标公告/政府采购'),
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/01/02/', '中标公告/政府采购'),
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/02/01/', '招标公告/建设工程'),
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/02/02/', '中标公告/建设工程'),
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/02/zjgczb/', '招标公告/街镇工程'),
        ('http://www.yw.gov.cn/zfmhwzxxgk/001/09/02/gczbgg/', '中标公告/街镇工程'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('div.news ul > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    # page_extractor = NodeValueExtractor(css=('div.fx > script',), value_xpath='.//text()')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response) or ''
        # count, page = SpiderTool.re_nums('I\.com\(\)\.pager\((\d+),(\d+),', pager)
        # page += 1
        # if page < count:
        #     url = response.url
        #     url = url[:url.rfind('/')] + '/index_{}.shtml'.format(page)
        #     yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.html') or response.css('epointform') or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('#gkdate'), body)
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.name'))
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

