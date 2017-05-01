import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class ZhejiangShaoxing1Spider(scrapy.Spider):
    """
    @title: 绍兴公共资源交易网
    @href: http://www.sxztb.gov.cn/sxweb/default.aspx
    """
    name = 'zhejiang/shaoxing/1'
    alias = '浙江/绍兴'
    allowed_domains = ['sxztb.gov.cn']
    start_urls = [
        # ('http://www.sxztb.gov.cn/sxweb/jsxm/002007/002007001/002007001001/', '招标公告/建设工程'),
        # ('http://www.sxztb.gov.cn/sxweb/jsxm/002007/002007001/002007001002/', '招标公告/建设工程'),
        # ('http://www.sxztb.gov.cn/sxweb/jsxm/002007/002007003/', '中标公告/建设工程'),
        # ('http://www.sxztb.gov.cn/sxweb/jsxm/002007/002007007/002007007001/', '招标公告/建设工程/区县'),
        # ('http://www.sxztb.gov.cn/sxweb/jsxm/002007/002007007/002007007003/', '中标公告/建设工程/区县'),
        ('http://www.sxztb.gov.cn/sxweb/zfcg/003007/003007002/', '招标公告/政府采购'),
        # ('http://www.sxztb.gov.cn/sxweb/zfcg/003007/003007003/', '中标公告/政府采购'),
        # ('http://www.sxztb.gov.cn/sxweb/zfcg/003007/003007008/003007008002/', '招标公告/政府采购/区县'),
        # ('http://www.sxztb.gov.cn/sxweb/zfcg/003007/003007008/003007008003/', '中标公告/政府采购/区县'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="20"] > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#spnShow') or response.css('#TDContent, div.infodetail')
        prefix = '^【\w{1,12}】'
        pid = '\([A-Z0-9-]+\)'

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        title = re.sub(pid, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
