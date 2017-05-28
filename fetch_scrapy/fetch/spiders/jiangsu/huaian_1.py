import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class huaian_1Spider(scrapy.Spider):
    """
    @title: 淮安市公共资源交易中心
    @href: http://www.haztb.gov.cn:8000/epointweb/
    """
    name = 'jiangsu/huaian/1'
    alias = '江苏/淮安'
    allowed_domains = ['haztb.gov.cn']
    start_urls = [
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003001/003001001/', '招标公告/建设工程', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003001/003001002/', '中标公告/建设工程', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003002/003002001/', '招标公告/政府采购', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003002/003002005/', '中标公告/政府采购', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003002/003002004/', '其他公告/废标公告', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003004/003004001/', '招标公告/机电设备', ''),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003004/003004003/', '中标公告/机电设备', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003006/003006001/', '招标公告/药械采购', ''),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003006/003006003/', '中标公告/药械采购', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003007/003007001/', '招标公告/其他项目', ''),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003007/003007002/', '中标公告/其他项目', ''),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009001/003009001001/', '招标公告/区县', '清江浦'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009001/003009001002/', '中标公告/区县', '清江浦'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009003/003009003001/', '招标公告/区县', '淮阴'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009003/003009003002/', '中标公告/区县', '淮阴'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009004/003009004001/', '招标公告/区县', '淮安'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009004/003009004002/', '中标公告/区县', '淮安'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009005/003009005001', '招标公告/区县', '涟水'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009005/003009005002', '中标公告/区县', '涟水'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009006/003009006001', '招标公告/区县', '洪泽'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009006/003009006002', '中标公告/区县', '洪泽'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009007/003009007001', '招标公告/区县', '盱眙'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009007/003009007002', '中标公告/区县', '盱眙'),
        ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009008/003009008001', '招标公告/区县', '金湖'),
        # ('http://www.haztb.gov.cn:8000/EpointWeb/jyxx/003009/003009008/003009008002', '中标公告/区县', '金湖'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.38}

    def start_requests(self):
        for url, subject, area in self.start_urls:
            data = dict(subject=subject, area=area)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='ul.menu-right-items > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#mainContent') or response.css('.article-block')

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
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
