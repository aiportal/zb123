import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class hebei_1Spider(scrapy.Spider):
    """
    @title: 河北省政府采购网
    @href: http://www.ccgp-hebei.gov.cn/
    """
    name = 'hebei/1'
    alias = '河北'
    allowed_domains = ['ccgp-hebei.gov.cn']
    start_urls = [
        ('http://www.ccgp-hebei.gov.cn/province/cggg/zbgg/', '招标公告/政府采购'),
        ('http://www.ccgp-hebei.gov.cn/province/cggg/fbgg/', '废标公告/政府采购'),
        ('http://www.ccgp-hebei.gov.cn/province/cggg/zhbgg/', '中标公告/政府采购'),
        ('http://www.ccgp-hebei.gov.cn/province/cggg/gzgg/', '更正公告/政府采购'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.08}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#moredingannctable tr > td > a',
                                    attrs_xpath={'text': './/text()',
                                                 'day': '../../following-sibling::tr[1]/td/span[1]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table[bgcolor="#bfdff1"], span.txt7:not([id]), a.blue')

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
