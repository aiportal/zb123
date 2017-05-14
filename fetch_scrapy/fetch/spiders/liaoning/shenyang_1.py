import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class shenyang_1Spider(scrapy.Spider):
    """
    @title: 沈阳公共资源交易监督管理信息网
    @href: http://sy1.lnzb.cn/syxx/
    """
    name = 'liaoning/shenyang/1'
    alias = '辽宁/沈阳'
    allowed_domains = ['syjy.gov.cn']
    start_urls = [
        ('http://www.syjy.gov.cn/NoticeTab/Tab_Zfcg_tab1_Sj', '招标公告/政府采购'),
        ('http://www.syjy.gov.cn/NoticeTab/Tab_Zfcg_tab2_Sj', '中标公告/政府采购'),
        ('http://www.syjy.gov.cn/NoticeTab/Tab_Jsgc_tab1_Sj', '招标公告/建设工程'),
        ('http://www.syjy.gov.cn/NoticeTab/Tab_Jsgc_tab2_Sj', '中标公告/建设工程'),

        ('http://www.syjy.gov.cn/NoticeTabQx/Tab_Zfcg_tab1_Qx', '招标公告/政府采购/区县'),
        ('http://www.syjy.gov.cn/NoticeTabQx/Tab_Zfcg_tab2_Qx', '中标公告/政府采购/区县'),
        ('http://www.syjy.gov.cn/NoticeTabQx/Tab_Jsgc_tab1_Qx', '招标公告/建设工程/区县'),
        ('http://www.syjy.gov.cn/NoticeTabQx/Tab_Jsgc_tab2_Qx', '中标公告/建设工程/区县'),
    ]

    link_extractor = MetaLinkExtractor(css='div.list_mb_list_aa > a[target=_blank]',
                                       attrs_xpath={'text': './/text()',
                                                    'day': '../../div[@class="list_mb_list_ba"]//text()'})

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
        body = response.css('#Zoom')
        prefix = '^【\w{2,8}】'

        day = FieldExtractor.date(data.get('day'), response.css('div.more_annotation'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        if title.endswith('...'):
            title1 = FieldExtractor.text(response.css('div.more_title'))
            title = title1 or title
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
