import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class neimenggu_2Spider(scrapy.Spider):
    """
    @title: 内蒙古自治区公共资源交易网
    @href: http://www.nmgggzyjy.gov.cn/
    """
    name = 'neimenggu/2'
    alias = '内蒙古'
    allowed_domains = ['nmgggzyjy.gov.cn']
    start_urls = [
        ('http://www.nmgggzyjy.gov.cn/jyxx/zfcg/cggg', '招标公告/政府采购', a, {'area': k})
        for k, a in [
            ('001', '自治区'),
            ('002', '呼和浩特市'),
            # ('003', '包头市'),
            ('004', '呼伦贝尔市'),
            ('005', '兴安盟'),
            ('006', '通辽市'),
            # ('007', '赤峰市'),
            ('008', '锡林郭勒盟'),
            # ('009', '乌兰察布市'),
            # ('010', '鄂尔多斯市'),
            ('011', '巴彦淖尔市'),
            # ('012', '乌海市'),
            ('013', '阿拉善盟'),
            # ('014', '满洲里市'),
            # ('015', '二连浩特市'),
        ]
    ] + [
        ('http://www.nmgggzyjy.gov.cn/jyxx/jsgcZbgg', '招标公告/建设工程', a, {'area': k})
        for k, a in [
            ('001', '自治区'),
            ('002', '呼和浩特市'),
            ('003', '包头市'),
            ('004', '呼伦贝尔市'),
            # ('005', '兴安盟'),
            ('006', '通辽市'),
            # ('007', '赤峰市'),
            ('008', '锡林郭勒盟'),
            # ('009', '乌兰察布市'),
            # ('010', '鄂尔多斯市'),
            # ('011', '巴彦淖尔市'),
            # ('012', '乌海市'),
            ('013', '阿拉善盟'),
            # ('014', '满洲里市'),
            # ('015', '二连浩特市'),
        ]

        # ('http://www.nmgggzyjy.gov.cn/jyxx/zfcg/zbjggs', '中标公告/政府采购'),
        # ('http://www.nmgggzyjy.gov.cn/jyxx/zfcg/gzsx', '更正公告/政府采购'),
        # ('http://www.nmgggzyjy.gov.cn/jyxx/jsgcZbjggs', '中标公告/建设工程'),
        # ('http://www.nmgggzyjy.gov.cn/jyxx/jsgcGzsx?industriesTypeCode=000', '更正公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.list-ask tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject, area, param in self.start_urls:
            data = dict(subject=subject, area=area)
            yield scrapy.FormRequest(url, formdata=param, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.detail_contect')

        day = FieldExtractor.date(data.get('day') or response.css('div.tip'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
