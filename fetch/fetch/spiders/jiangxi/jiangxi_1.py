import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class Jiangxi1Spider(scrapy.Spider):
    """
    @title: 江西省公共资源交易网
    @href: http://www.jxsggzy.cn/web/
    """
    name = 'jiangxi/1'
    alias = '江西'
    allowed_domains = ['jxsggzy.cn']
    start_urls = [
        ('http://www.jxsggzy.cn/web/jyxx/002001/002001001/jyxx.html', '招标公告/市政工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002001/002001004/jyxx.html', '中标公告/市政工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002002/002002002/jyxx.html', '招标公告/交通工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002002/002002005/jyxx.html', '中标公告/交通工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002003/002003001/jyxx.html', '招标公告/水利工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002003/002003004/jyxx.html', '中标公告/水利工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002005/002005001/jyxx.html', '招标公告/重点工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002005/002005004/jyxx.html', '中标公告/重点工程'),
        ('http://www.jxsggzy.cn/web/jyxx/002006/002006001/jyxx.html', '招标公告/政府采购'),
        ('http://www.jxsggzy.cn/web/jyxx/002006/002006004/jyxx.html', '中标公告/政府采购'),
        ('http://www.jxsggzy.cn/web/jyxx/002010/002010001/jyxx.html', '招标公告/医药采购'),
        ('http://www.jxsggzy.cn/web/jyxx/002010/002010002/jyxx.html', '中标公告/医药采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.ewb-infolist ul > li > a',
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
        contents = response.css('div.article-info div.con').extract()

        # if response.body[:4] == b'%PDF':
        #     contents = ['<a href="{}" target="_blank">招标公告</a>'.format(response.url)]
        # else:
        #     body = response.css('#TDContent') or response.css('.infodetail')
        #     contents = body.extract()
        prefix = '^\[\w{2,15}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(contents))
        return [g]
