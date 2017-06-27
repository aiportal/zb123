import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shenhuaSpider(scrapy.Spider):
    """
    @title: 神华招标网
    @href: http://www.shenhuabidding.com.cn/bidweb/
    """
    name = 'other/shenhua/1'
    alias = '其他/神华'
    allowed_domains = ['shenhuabidding.com.cn']
    start_urls = [
        ('http://www.shenhuabidding.com.cn/bidweb/001/001002/moreinfo.html', '招标公告'),
        ('http://www.shenhuabidding.com.cn/bidweb/001/001006/moreinfo.html', '中标公告'),
        ('http://www.shenhuabidding.com.cn/bidweb/001/001004/moreinfo.html', '更正公告'),
    ]

    link_extractor = MetaLinkExtractor(css='div.right-bd > ul > li a.infolink',
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
        body = response.css('div.article-info')

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
