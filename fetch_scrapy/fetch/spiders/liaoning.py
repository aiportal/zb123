import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class LiaoningSpider(HtmlMetaSpider):
    name = 'liaoning'
    alias = '辽宁'
    allowed_domains = ['lnzc.gov.cn']
    start_referer = None
    start_pages = [
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll1.aspx', {'subject': '招标公告'}),
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll2.aspx', {'subject': '中标公告'}),
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll3.aspx', {'subject': '更正公告'}),
    ]
    start_params = {}
    custom_settings = {'COOKIES_ENABLED': True}

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='ul.infoList > li > span > a[href^="/oa/bs/"]', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../span[1]//text()'})
    # 翻页链接
    page_extractor = NodeValueExtractor(css='td.ms-paging > a > img[src$="next.gif"]',
                                        value_xpath='../@href', value_regex="__doPostBack\('(.+)','(.+)'\)")

    def start_requests(self):
        for url, data in self.start_pages:
            yield scrapy.Request(url, meta={'params': data}, dont_filter=True)

    def page_requests(self, response):
        event_target, event_argument = self.page_extractor.extract_value(response)
        form = {
            '__EVENTTARGET': event_target,
            '__EVENTARGUMENT': event_argument
        }
        yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start', '').replace('/', '-'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('#WebPartWPQ1 > div[class^=ExternalClass] > *',
                                                      '#WebPartWPQ1 > div[class^=ExternalClass] > * > *'))
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
