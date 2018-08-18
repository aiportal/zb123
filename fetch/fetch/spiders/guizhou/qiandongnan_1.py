import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class qiandongnan_1Spider(scrapy.Spider):
    """
    @title: 黔东南州公共资源交易网
    @href: http://www.qdnggzy.cn/qdnztb/
    """
    name = 'guizhou/qiandongnan/1'
    alias = '贵州/黔东南'
    allowed_domains = ['qdnggzy.cn']
    start_urls = [
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056002/056002001/', '招标公告/政府采购'),
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056002/056002003/', '中标公告/政府采购'),
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056002/056002004/', '废标公告/政府采购'),
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056001/056001001/', '招标公告/建设工程'),
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056001/056001004/', '中标公告/建设工程'),
        ('http://www.qdnggzy.cn/qdnztb/jyxx/056001/056001005/', '废标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='#erj tr>td>a[target=_blank]',
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
        body = response.css('#TDContent, #filedown')
        prefix = '^\[\w{2,8}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
