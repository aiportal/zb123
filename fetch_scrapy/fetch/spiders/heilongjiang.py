import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class HeilongjiangSpider(HtmlMetaSpider):
    name = 'heilongjiang'
    alias = '黑龙江'
    allowed_domains = ['hljcg.gov.cn']
    start_referer = 'http://www.hljcg.gov.cn/xwzs!index.action'
    start_urls = ['http://www.hljcg.gov.cn/xwzs!queryXwxxqx.action']
    start_params = {
        'lbbh': {'4': '招标公告', '30': '更正公告', '5': '中标公告'},
        'xwzsPage.pageNo': {1: None},
        'xwzsPage.pageSize': {100: None},
    }
    custom_settings = {'COOKIES_ENABLED': True}

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.yahoo > div.xxei > span.lbej > a', url_attr='onclick',
                                       attrs_xpath={'text': './text()', 'start': '../../span[@class="sjej"]//text()'},
                                       url_process=lambda x: str(x or '')
                                       .replace("javascript:location.href='", '')
                                       .replace("';return false;", ''))
    # 翻页链接
    page_extractor = NodeValueExtractor(css='div.yahoo2 > div.list-page > a:contains(下页)', value_xpath='./@onclick',
                                        value_regex='(\d+)')

    def start_requests(self):   # 先访问主页，获得Cookie
        yield scrapy.Request(self.start_referer, callback=self.start_requests_real)

    def start_requests_real(self, response):
        return super().start_requests()

    def page_requests(self, response):
        page = self.page_extractor.extract_value(response)
        if page:
            url = self.replace_url_param(response.url, **{'xwzsPage.pageNo': page})
            yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('lbbh'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('div.xxej > * > *',))
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
