import scrapy
from .. import HtmlMetaSpider, GatherItem
from .. import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class ShandongSpider(HtmlMetaSpider):
    name = 'shandong'
    alias = '山东'
    allowed_domains = ["ccgp-shandong.gov.cn"]
    start_referer = None
    start_urls = ['http://www.ccgp-shandong.gov.cn/sdgp2014/site/channelall.jsp']
    start_params = {
        'colcode': {'0301': '招标公告/省招标公告', '0302': '中标公告/省中标公告', '0303': '招标公告/市县招标公告',
                    '0304': '中标公告/市县中标公告', '0305': '更正公告/信息更正', '0306': '其他公告/废标公告',
                    '0307': '其他公告/资格预审公告'}
    }
    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='td.Font9 > a.five', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='td.Font9 > a:contains(下一页)', url_attr='href')

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('colcode'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('td.aa > *', 'td[bgcolor="#FFFFFF"] > table[width="100%"] tr'))
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
