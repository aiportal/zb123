import scrapy
from .. import HtmlMetaSpider, GatherItem
from .. import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class QinghaiSpider(HtmlMetaSpider):
    name = 'qinghai'
    alias = '青海'
    allowed_domains = ["ccgp-qinghai.gov.cn"]
    start_referer = None
    start_urls = ['http://www.ccgp-qinghai.gov.cn/jilin/zbxxController.form']
    start_params = {
        'declarationType': {
            'GKZBGG': '招标公告/公开招标',
            'YQZBGG': '招标公告/邀请招标',
            'JZXTPGG': '招标公告/竞争性谈判',
            'JCGG': '招标公告/竞争性磋商',
            'XJZBGG': '招标公告/询价采购',
            'DYGG': '招标公告/单一来源',
            'W': '中标公告',
            'C': '更正公告/变更公告',
            'F': '其他公告/废流标公告',
            # 'YSGG': '其他公告/资格预审公告',
        },
        'type': {0: None},  # {1: '省级', 2: '市县'}
        'pageNo': {0: None}
    }
    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.m_list_3 > ul > li > div.news_list > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../div[1]//text()'},
                                       url_process=lambda x: '/' + str(x or '').split('=')[-1:][0])
    # 翻页链接
    page_extractor = MetaLinkExtractor(css='div.m_list_3 ~ div > a:contains(下一页)', url_attr='href')

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('declarationType'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('body > div.Section1 > *', 'body > div.WordSection1 > *', 'body > *'))
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)

        # 附件
        # files_extractor = FileLinkExtractor(css='#file_list a', attrs_css={'text': './text()'})
        # g['attachments'] = [f for f in files_extractor.extract_files(response)]
        yield g
