import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class ZhejiangSpider(HtmlMetaSpider):
    name = 'zhejiang'
    alias = '浙江'
    allowed_domains = ["zjzfcg.gov.cn"]
    start_referer = 'http://www.zjzfcg.gov.cn/new/cggg/index.htm'
    start_urls = ['http://www.zjzfcg.gov.cn/new/articleSearch/search_search.do']
    start_params = {
        'chnlIds': {'206,210': '预公告/采购预告',
                    '207,211': '招标公告/采购公告',
                    '208,212': '中标公告/中标成交公示',
                    '209,213': '中标公告/中标成交公告',
                    '401,411': '其他公告/采购合同公告',
                    '402,412': '其他公告/竞争性磋商公告',
                    '245': '其他公告/单一来源公示',
                    '445,400,410': '其他公告/进口产品公示',
                    '246,405,415': '其他公告/采购文件或需求公示'},
        'count': 30
    }

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.artcon_new > li > a:last-child',
                                       attrs_xpath={'text': './text()',
                                                    'area': '../a[1]/text()',
                                                    'industry': '../a[2]/text()',
                                                    'end': '../span/text()'})

    page_extractor = MetaLinkExtractor(css='div.artcon_new > div > a:contains(下一页)')

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(NodeValueExtractor.extract_text(response.css('#news_msg ::text')))
        g['end'] = DateExtractor.extract(data.get('end'))
        g['title'] = data.get('title') or data.get('text')
        g['area'] = data.get('area', '').strip('[]')
        g['subject'] = data.get('chnlIds')
        g['industry'] = data.get('industry', '').strip('[]')

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='#news_content > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)

        yield g
