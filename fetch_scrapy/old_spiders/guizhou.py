import scrapy
from .. import HtmlMetaSpider, GatherItem
from .. import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class GuizhouSpider(HtmlMetaSpider):
    name = 'guizhou'
    alias = '贵州'
    allowed_domains = ['ccgp-guizhou.gov.cn']
    start_pages = [
        ('http://www.ccgp-guizhou.gov.cn/list-{0}.html'.format(k), {'id': k, 'subject': v}) for k, v in
        {
            '1153418052184995': '招标公告/省级',
            '1153454200156791': '更正公告/省级',
            '1153531755759540': '中标公告/省级',
            '1153488085289816': '其他公告/废标公告/省级',
            '1153567415242344': '其他公告/单一来源公示/省级',
            '1153595823404526': '其他公告/单一来源(成交)公告/省级',
            '1153797950913584': '招标公告/市县',
            '1153905922931045': '中标公告/市县',
            '1153817836808214': '更正公告/市县',
            '1153845808113747': '其他公告/废标公告/市县',
            '1153924595764135': '其他公告/单一来源公示/市县',
            '1153937977184763': '其他公告/单一来源(成交)公告/市县'
        }.items()
    ]

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.xnrx > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()'})
    # 翻页链接
    page_extractor = NodeValueExtractor(css='div.page a:contains(下一页)', value_xpath='./@onclick')

    def start_requests(self):
        for url, data in self.start_pages:
            yield scrapy.Request(url, meta={'params': data}, dont_filter=True)

    def page_requests(self, response):
        values = self.page_extractor.extract_values(response)
        if values and values[0]:
            page = re.search('(\d+)', values[0]).group(1)
            yield scrapy.FormRequest.from_response(response, formid='articleSearchForm', formdata={'articlePageNo': page},
                                                   meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # TODO: 正文使用半角冒号分隔标题和内容，未提取到摘要信息(digest)

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start', '').replace('.', '-'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('#info > ul > *', '#info > *', 'div[align=left] > * > *'))
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
