import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class hubei_2Spider(scrapy.Spider):
    """
    @title: 湖北公共资源交易信息网
    @href: http://www.hbggzy.cn/hubeizxwz/
    """
    name = 'hubei/2'
    alias = '湖北'
    allowed_domains = ['hbggzy.cn']
    start_urls = [
        ('http://www.hbggzy.cn/jydt/003001/003001001/moreinfo_jyxx.html', '预公告'),
        ('http://www.hbggzy.cn/jydt/003001/003001002/moreinfo_jyxx.html', '招标公告'),
        ('http://www.hbggzy.cn/jydt/003001/003001005/moreinfo_jyxx.html', '中标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='ul.ewb-news-items > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.news-article-para')
        prefix = '^\[\w{2,8}\]|^<font .+</font>'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
