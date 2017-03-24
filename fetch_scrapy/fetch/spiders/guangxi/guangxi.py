import scrapy
from .. import HtmlMetaSpider
from fetch.extractors import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, MoneyExtractor
import re


# 'http://www.gxgp.gov.cn/ygswz/index.htm',       # 预公告
# 'http://www.gxgp.gov.cn/cggkzb/index.htm',      # 采购公告
# 'http://www.gxgp.gov.cn/zbgkzb/index.htm',      # 中标公告


class GuangxiSpider(HtmlMetaSpider):
    name = 'guangxi'
    alias = '广西'
    allowed_domains = ["gxgp.gov.cn"]
    start_referer = None
    start_urls = ['http://www.gxgp.gov.cn/']
    start_params = {
        'subject': {
            'ygswz/index.htm': '预公告/预公示',
            'cggkzb/index.htm': '招标公告/公开招标', 'cgjz/index.htm': '招标公告/竞争性谈判',
            'cgdyly/index.htm': '招标公告/单一来源', 'cgxjcg/index.htm': '招标公告/询价采购',
            'zbgkzb/index.htm': '中标公告/公开招标', 'zbjz/index.htm': '中标公告/竞争性谈判',
            'zbdyly/index.htm': '中标公告/单一来源', 'zbxjcg/index.htm': '中标公告/询价采购',
        }
    }

    def start_requests(self):
        for k, v in self.start_params['subject'].items():
            url = self.start_urls[0] + k
            yield scrapy.Request(url, meta={'params': {'subject': v}})

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.list_content div.c1-bline a', url_attr='href',
                                       attrs_xpath={'text': './/text()', 'start': '../../div[@class="f-right"]//text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='div.pg-3 > a:contains(下一页)', url_attr='href')

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='div.pbox > div > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = MoneyExtractor.money_max(response.css('div.pbox'))
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)

        yield g
