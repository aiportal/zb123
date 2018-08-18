import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class huadianSpider(scrapy.Spider):
    """
    @title: 华电集团电子商务平台
    @href: http://www.chdtp.com/
    """
    name = 'other/huadian/1'
    alias = '其他/华电'
    allowed_domains = ['chdtp.com']
    start_urls = [
        ('http://www.chdtp.com/webs/queryWebZbgg.action?zbggType=0', '招标公告/自主招标'),
        ('http://www.chdtp.com/webs/queryWebZbgg.action?zbggType=1', '招标公告/代理招标'),
    ]

    link_extractor = NodesExtractor(css='tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            href = SpiderTool.re_text("toGetContent\('(.+)'\)", row['href'])
            url = urljoin(response.url, '/staticPage/' + href)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('td.text_zx')

        day = FieldExtractor.date(data.get('day'))
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
