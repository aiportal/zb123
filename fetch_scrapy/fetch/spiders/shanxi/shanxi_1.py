import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shanxi_1Spider(scrapy.Spider):
    """
    @title: 山西省政府采购中心
    @href: http://sxzfcg.cn/default.html
    """
    name = 'shanxi/1'
    alias = '山西'
    allowed_domains = ['sxzfcg.cn']
    start_urls = [
        ('http://www.sxzfcg.cn/view.php?nav=61', '招标公告/货物类'),
        ('http://www.sxzfcg.cn/view.php?nav=62', '招标公告/工程类'),
        ('http://www.sxzfcg.cn/view.php?nav=63', '招标公告/服务类'),
        ('http://www.sxzfcg.cn/view.php?nav=67', '中标公告/货物类'),
        ('http://www.sxzfcg.cn/view.php?nav=68', '中标公告/工程类'),
        ('http://www.sxzfcg.cn/view.php?nav=69', '中标公告/服务类'),
        ('http://www.sxzfcg.cn/view.php?nav=64', '更正公告/货物类'),
        ('http://www.sxzfcg.cn/view.php?nav=65', '更正公告/工程类'),
        ('http://www.sxzfcg.cn/view.php?nav=66', '更正公告/服务类'),
    ]

    link_extractor = MetaLinkExtractor(css='#node_list tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#show')

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
