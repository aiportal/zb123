import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class sanming_1Spider(scrapy.Spider):
    """
    @title: 三明市公共资源交易网
    @href: http://www.smggzy.com/smwz/
    """
    name = 'fujian/sanming/1'
    alias = '福建/三明'
    allowed_domains = ['smggzy.com']
    start_urls = [
        ('http://www.smggzy.com/smwz/gcjsjy/010001/', '招标公告/建设工程'),
        ('http://www.smggzy.com/smwz/gcjsjy/010003/', '中标公告/建设工程'),
        ('http://www.smggzy.com/smwz/zfcg/011001/', '招标公告/政府采购'),
        ('http://www.smggzy.com/smwz/zfcg/011003/', '中标公告/政府采购'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 2.3}

    link_extractor = MetaLinkExtractor(css='.infocont tr > td > a[target=_blank]',
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
        prefix = '^[A-Z][A-Z0-9-]{8,18}'

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
