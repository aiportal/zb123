import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class zhongwei_1Spider(scrapy.Spider):
    """
    @title: 中卫市公共资源交易中心
    @href: http://www.zwsggzy.cn/zwsggzy/
    """
    name = 'ningxia/zhongwei/1'
    alias = '宁夏/中卫'
    allowed_domains = ['zwsggzy.cn']
    start_urls = [
        ('http://www.zwsggzy.cn/zwsggzy/003/003001/list.html', '招标公告/政府采购'),
        ('http://www.zwsggzy.cn/zwsggzy/004/004001/list.html', '中标公告/政府采购'),
        ('http://www.zwsggzy.cn/zwsggzy/003/003002/list.html', '招标公告/建设工程'),
        ('http://www.zwsggzy.cn/zwsggzy/004/004002/list.html', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.lmright ul > li > a[id^=Rep_morelink]',
                                       attrs_xpath={'text': './text()', 'day': './span//text()'})

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
        body = response.css('ul.a_content')
        prefix = '^\[\w{2,8}\]'
        suffix = '\[\w{2,8}\]$'

        day = FieldExtractor.date(data.get('day') or response.css('p.box_p'))
        title = data.get('title') or data.get('text')
        if title.endswith('...'):
            title1 = FieldExtractor.text(response.css('#Label_top'))
            if len(title)-3 < len(title1) < 200:
                title = title1 or title
        title = re.sub(prefix, '', title)
        title = re.sub(suffix, '', title)
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
