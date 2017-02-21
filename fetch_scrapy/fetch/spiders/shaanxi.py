import scrapy
from . import HtmlMetaSpider, GatherItem
from . import MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class ShaanxiSpider(HtmlMetaSpider):
    name = 'shaanxi'
    alias = '陕西'
    allowed_domains = ['ccgp-shaanxi.gov.cn']
    start_referer = 'http://www.ccgp-shaanxi.gov.cn/index.jsp'
    start_urls = {
        subject: url.format(code)
        for url in [
            'http://www.ccgp-shaanxi.gov.cn/saveData.jsp?ClassBID={0}&type=AllView',
            'http://www.ccgp-shaanxi.gov.cn/saveDataDq.jsp?ClassBID={0}&type=AllViewDq'
        ]
        for code, subject in {
            'D0003': '招标公告/询价公告',
            'C0001': '招标公告',
            'E0001': '更正公告/变更公告',
            'C0002': '中标公告',
            'D0001': '中标公告/谈判成交',
            'CS002': '中标公告/磋商成交',
            # 'DY001': '中标公告/单一成交',
            'XC001': '中标公告/询价成交',            ''
            'D0002': '其他公告/谈判公告',
            'CS001': '其他公告/磋商公告',
            'FB001': '其他公告/废标公告',
        }.items()
    }
    start_params = {}
    custom_settings = {'COOKIES_ENABLED': True}

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='table.tab tr > td.xian > a.b', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../td[last()]//text()'})
    # 翻页链接
    page_extractor = MetaLinkExtractor(css='form[name=formBean] a:contains(下一页)', url_attr='href')

    def start_requests(self):
        for subject, url in self.start_urls.items():
            yield scrapy.Request(url, meta={'params': {'subject': subject}})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start', '').strip('[]'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        # content_extractor = HtmlContentExtractor(css=('td.aa > *', 'td[bgcolor="#FFFFFF"] > table[width="100%"] tr'))
        content_extractor = HtmlContentExtractor(xpath=('(//table[@class="td"])[2]/tr/td/*',
                                                        '(//table[@class="td"])[2]/tr/td//p'))
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
