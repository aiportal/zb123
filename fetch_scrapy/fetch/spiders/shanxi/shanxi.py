import scrapy
from .. import HtmlMetaSpider, GatherItem
from fetch.extractors import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class ShanxiSpider(HtmlMetaSpider):
    name = 'shanxi'
    alias = '山西'
    allowed_domains = ["sxzfcg.cn"]
    start_referer = None
    start_urls = ['http://www.sxzfcg.cn/view.php']
    start_params = {
        'nav': {'61': '招标公告/货物类', '62': '招标公告/工程类', '63': '招标公告/服务类',
                '64': '更正公告/货物类', '65': '更正公告/工程类', '66': '更正公告/服务类',
                '67': '中标公告/结果公告/货物类', '68': '中标公告/结果公告/工程类', '69': '中标公告/结果公告/服务类'},
        'page': {1: None}
    }

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='#node_list tr > td > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../td[2]//text()'})
    # 翻页链接
    page_extractor = MetaLinkExtractor(css='div.pager > a:contains(后一页)', url_attr='href')

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('nav'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='#show > *')
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
