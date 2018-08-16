import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


# 安徽省政府采购
# http://www.ahzfcg.gov.cn/

default_url = 'http://www.ahzfcg.gov.cn/cmsNewsController/getCgggNewsList.do'

class AnhuiNewSpider(scrapy.Spider):
    name = 'anhui/1'
    alias = '安徽'
    allow_domains = ['ahzfcg.gov.cn']
    start_urls = [
        (default_url + '?channelCode=sjcg_cggg&bid_type=011&type=101', '招标公告/采购公告'),
        (default_url + '?channelCode=sjcg_gzgg&bid_type=110&type=101', '更正公告'),
        (default_url + '?channelCode=sjcg_zbgg&bid_type=108&type=101', '中标公告'),
        (default_url + '?channelCode=sjcg_cjgg&bid_type=112&type=101', '成交公告'),
        (default_url + '?channelCode=sjcg_zzgg&bid_type=113&type=101', '废标公告'),
        (default_url + '?channelCode=sjcg_qtgg&bid_type=107&type=101', '其他公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.zc_contract_top tr > td > a[target]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.frameNews')

        day = FieldExtractor.date(data.get('day'), body)
        title = data.get('title') or data.get('text')
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
