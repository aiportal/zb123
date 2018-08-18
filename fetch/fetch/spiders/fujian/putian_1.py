import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class putian_1Spider(scrapy.Spider):
    """
    @title: 莆田行政服务中心
    @href: http://www.ptfwzx.gov.cn/fwzx/
    """
    name = 'fujian/putian/1'
    alias = '福建/莆田'
    allowed_domains = ['ptfwzx.gov.cn']
    start_urls = [
        ('http://www.ptfwzx.gov.cn/fwzx/wjzyzx/004002/004002005/', '招标公告/建设工程'),
        ('http://www.ptfwzx.gov.cn/fwzx/wjzyzx/004002/004002010/', '中标公告/建设工程'),
        ('http://www.ptfwzx.gov.cn/fwzx/wjzyzx/004003/004003002/004003002005/', '招标公告/政府采购/公开招标'),
        ('http://www.ptfwzx.gov.cn/fwzx/wjzyzx/004003/004003006/004003006005/', '中标公告/政府采购/公开招标'),
    ]

    link_extractor = MetaLinkExtractor(css='div.main tr>td>a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent, #trAttach')

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
