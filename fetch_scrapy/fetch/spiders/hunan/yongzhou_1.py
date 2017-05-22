import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class yongzhou_1Spider(scrapy.Spider):
    """
    @title: 永州市公共资源交易网
    @href: http://ggzy.yzcity.gov.cn/yzweb/
    """
    name = 'hunan/yongzhou/1'
    alias = '湖南/永州'
    allowed_domains = ['yzcity.gov.cn']
    start_urls = [
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004002/004002001/', '招标公告/政府采购'),
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004002/004002004/', '中标公告/政府采购'),
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004002/004002002/', '更正公告/政府采购'),
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004001/004001001/', '招标公告/建设工程'),
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004001/004001004/', '中标公告/建设工程'),
        ('http://ggzy.yzcity.gov.cn/yzweb/jyxx/004001/004001002/', '更正公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='td.moreinfo tr > td > span > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../../td[last()]//text()'})

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
        if re.match('<script.+</script>', response.text):
            href = SpiderTool.re_text("location='(.+)'", response.text)
            url = urljoin(response.url, href)
            body = ['<a href="{}">招标文件</a>'.format(url)]
        else:
            body = response.css('#TDContent, #trAttach').extract()

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body
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
