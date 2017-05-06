import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class nanping_1Spider(scrapy.Spider):
    """
    @title: 南平市公共资源交易中心
    @href: http://www.npggzy.gov.cn/npztb/
    """
    name = 'fujian/nanping/1'
    alias = '福建/南平'
    allowed_domains = ['npggzy.gov.cn', 'npzbtb.gov.cn']
    start_urls = [
        ('http://www.npggzy.gov.cn/npztb/jsgc/010001/', '招标公告/建设工程', 0),
        ('http://www.npggzy.gov.cn/npztb/jsgc/010005/', '中标公告/建设工程', 0),
        # ('', '招标公告/政府采购'),
        # ('', '中标公告/政府采购'),
        ('http://www.npggzy.gov.cn/npztb/qxzbxx/013001/', '招标公告/企业', 1),
        ('http://www.npggzy.gov.cn/npztb/qxzbxx/013005/', '中标公告/企业', 1),
    ]

    link_extractors = (
        MetaLinkExtractor(css='div.main-subcontent tr > td > a[target=_blank]',
                          attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'}),
        MetaLinkExtractor(css='ul.content-list > li > a',
                          attrs_xpath={'text': './span[@class="link-content"]//text()',
                                       'day': './span[@class="time"]//text()'}),
    )

    def start_requests(self):
        for url, subject, extractor in self.start_urls:
            data = dict(subject=subject, extractor=extractor)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        extractor = self.link_extractors[response.meta['data']['extractor']]    # type: MetaLinkExtractor
        links = extractor.links(response)
        assert len(links)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#JszbggDetail1_content, #JsbctzDetail1_content, JszbgsDetail1_content') \
            or response.css('#menutab_6_1, #menutab_6_2, #menutab_6_5') \
            or response.css('#mainContent')

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
