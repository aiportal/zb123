import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


# 中国联通采购与招标网
# http://www.chinaunicombidding.cn/

class LiantongSpider(scrapy.Spider):
    name = 'other/liantong'
    alias = '其他/中国联通'
    start_urls = [
        # ('http://www.chinaunicombidding.cn/jsp/cnceb/web/info1/infoList.jsp?page=1', '招标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('span[onclick^="window.open("]',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[2]//text()',
                                                    'area': '../../td[3]//text()'})
    page_extractor = NodeValueExtractor(css=('#nowPage',), value_xpath='..//text()')

    def parse(self, response):
        nodes = self.link_extractor.extract_nodes(response)
        for node in nodes:
            href = SpiderTool.re_text('window.open\("(.+)","",', node['onclick'])
            url = urljoin(response.url, href)
            node.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': node}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page, count = SpiderTool.re_nums('第\s*(\d+)\s*页\s*共\s*(\d+)\s*页', pager)
        page += 1
        if page < count:
            url = SpiderTool.url_replace(response.url, page=page)
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('div.Section1 > table'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
