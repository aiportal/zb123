import scrapy
from . import HtmlMetaSpider, GatherItem
from . import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class JilinSpider(HtmlMetaSpider):
    name = 'jilin'
    alias = '吉林'
    allowed_domains = ['jlszfcg.gov.cn']
    start_referer = 'http://www.jlszfcg.gov.cn/html/zbxx/zbxx_index.html'
    start_urls = ['http://www.jlszfcg.gov.cn/jilin/zbxxController.form']
    start_params = {
        # 'bidWay': {'GKZB': '公开招标', 'YQZB': '邀请招标', 'JZXTP': '竞争性谈判',
        #            'XJCG': '询价采购', 'JZXCS': '竞争性磋商', 'DYCGLY': '单一来源'},
        'bidWay': {'': ''},
        'declarationType': {'ZHAOBGG': '招标公告'},
        'pageNo': {0: None}
    }
    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='div.con08_a ul > li > div a[href^="/html/"]', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../span//text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='div.sub_page a:contains(下一页)', url_attr='href')

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
        content_extractor = HtmlContentExtractor(css=('div.con08_b_c > div > *',))
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
