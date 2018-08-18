import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class wuhuSpider(scrapy.Spider):
    """
    @title: 芜湖市公共资源交易中心
    @href: http://www.whzbb.com.cn/whweb/default.aspx
    """
    name = 'anhui/wuhu/1'
    alias = '安徽/芜湖'
    allowed_domains = ['whzbb.com.cn']
    start_urls = [
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004001/013004001001/', '招标公告/建设工程/市级'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004001/013004001004/', '中标公告/建设工程/市级'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004002/013004002001/', '招标公告/政府采购/市级'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004002/013004002004/', '中标公告/政府采购/市级'),

        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004007/013004007001/', '招标公告/建设工程/区县/无为县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004007/013004007004/', '中标公告/建设工程/区县/无为县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004008/013004008001/', '招标公告/政府采购/区县/无为县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004008/013004008004/', '中标公告/政府采购/区县/无为县'),

        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004009/013004009001/', '招标公告/建设工程/区县/芜湖县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004009/013004009004/', '中标公告/建设工程/区县/芜湖县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004010/013004010001/', '招标公告/政府采购/区县/芜湖县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004010/013004010004/', '中标公告/政府采购/区县/芜湖县'),

        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004011/013004011001/', '招标公告/建设工程/区县/南陵县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004011/013004011004/', '中标公告/建设工程/区县/南陵县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004012/013004012001/', '招标公告/政府采购/区县/南陵县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004012/013004012004/', '中标公告/政府采购/区县/南陵县'),

        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004013/013004013001/', '招标公告/建设工程/区县/繁昌县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004013/013004013004/', '中标公告/建设工程/区县/繁昌县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004014/013004014001/', '招标公告/政府采购/区县/繁昌县'),
        ('http://www.whzbb.com.cn/whweb/jyzx/013004/013004014/013004014004/', '中标公告/政府采购/区县/繁昌县'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td.TDStyle > a',
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
        body = response.css('#TDContent, .infodetail, #trAttach')
        prefix = '^\[\w{1,8}\]'

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
