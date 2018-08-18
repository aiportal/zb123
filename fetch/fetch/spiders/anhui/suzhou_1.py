import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class suzhou_1Spider(scrapy.Spider):
    """
    @title: 宿州市公共资源交易网
    @href: http://www.szggzyjy.cn/szfront/
    """
    name = 'anhui/suzhou/1'
    alias = '安徽/宿州'
    allowed_domains = ['szggzyjy.cn']
    start_urls = [
        ('http://www.szggzyjy.cn/szfront/jyxx/002001/002001001/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/宿州市'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/宿州市'),
        ]),
        ('http://www.szggzyjy.cn/szfront/jyxx/002001/002001002/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/宿州市'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/宿州市'),
        ]),

        ('http://www.szggzyjy.cn/szfront/jyxx/002002/002002001/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/埇桥区'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/埇桥区'),
        ]),
        ('http://www.szggzyjy.cn/szfront/jyxx/002002/002002002/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/埇桥区'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/埇桥区'),
        ]),

        ('http://www.szggzyjy.cn/szfront/jyxx/002003/002003001/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/泗县'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/泗县'),
        ]),
        ('http://www.szggzyjy.cn/szfront/jyxx/002003/002003002/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/泗县'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/泗县'),
        ]),

        # ('http://www.szggzyjy.cn/szfront/jyxx/002004/002004001/', [
        #     ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/砀山县'),
        #     ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/砀山县'),
        # ]),
        # ('http://www.szggzyjy.cn/szfront/jyxx/002004/002004002/', [
        #     ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/砀山县'),
        #     ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/砀山县'),
        # ]),
        #
        # ('http://www.szggzyjy.cn/szfront/jyxx/002005/002005001/', [
        #     ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/萧县'),
        #     ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/萧县'),
        # ]),
        # ('http://www.szggzyjy.cn/szfront/jyxx/002005/002005002/', [
        #     ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/萧县'),
        #     ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/萧县'),
        # ]),

        ('http://www.szggzyjy.cn/szfront/jyxx/002006/002006001/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/建设工程/灵璧县'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/建设工程/灵璧县'),
        ]),
        ('http://www.szggzyjy.cn/szfront/jyxx/002006/002006002/', [
            ('//div[@class="con-box"]/div[@class="s-block"][1]//ul/li/a', '招标公告/政府采购/灵璧县'),
            ('//div[@class="con-box"]/div[@class="s-block"][2]//ul/li/a', '中标公告/政府采购/灵璧县'),
        ]),
    ]

    def start_requests(self):
        for url, subjects in self.start_urls:
            data = dict(subjects=subjects)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        for xpath, subject in data['subjects']:
            extractor = MetaLinkExtractor(xpath=xpath, attrs_xpath={'text': './/text()', 'day': '../span//text()'})
            links = extractor.links(response)
            # assert len(links) > 0
            for lnk in links:
                lnk.meta.update(subject=subject)
                yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#mainContent')
        prefix = '^\[\w{0,5}\]'

        day = FieldExtractor.date(data.get('day'), response.css('div.ewb-show-sub'))
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
