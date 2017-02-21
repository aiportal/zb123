import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodesExtractor, NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class HainanSpider(HtmlMetaSpider):
    name = 'hainan'
    alias = '海南'
    allowed_domains = ['ztb.sanya.gov.cn']  # 三亚
    start_referer = None
    start_urls = {
        '招标公告/政府采购': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001002/001002001/MoreInfo.aspx?CategoryNum=001002001',
        '更正公告/政府采购': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001002/001002002/MoreInfo.aspx?CategoryNum=001002002',
        '中标公告/政府采购': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001002/001002004/MoreInfo.aspx?CategoryNum=001002004',
        '其他公告/政府采购': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001002/001002005/MoreInfo.aspx?CategoryNum=001002005',
        '招标公告/工程建设': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001001/001001001/MoreInfo.aspx?CategoryNum=001001001',
        '更正公告/工程建设': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001001/001001002/MoreInfo.aspx?CategoryNum=001001002',
        '中标公告/工程建设': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001001/001001004/MoreInfo.aspx?CategoryNum=001001004',
        '其他公告/工程建设': 'http://ztb.sanya.gov.cn/sanyaztb/jyxx/001001/001001005/MoreInfo.aspx?CategoryNum=001001005',
    }
    custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for subject, url in self.start_urls.items():
            yield scrapy.Request(url, meta={'params': {'subject': subject}}, dont_filter=True)

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='table#MoreInfoList1_DataGrid1 tr > td > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../../td[last()]//text()'})

    page_extractor = NodeValueExtractor(css='#MoreInfoList1_Pager a > img[src$="nextn.gif"]',
                                        value_xpath='../@href', value_regex='\'(\d+)\'\)')

    def page_requests(self, response):
        page = self.page_extractor.extract_value(response)
        if page:
            form = {'__EVENTTARGET': 'MoreInfoList1$Pager', '__EVENTARGUMENT': page}
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias, data.get('area'))
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('#TDContent > *:not(style)', '#TDContent p, #TDContent table'))
        g['contents'] = content_extractor.extract_contents(response)
        if not g['contents']:
            g['contents'] = NodesExtractor.extract_text(response.css('#TDContent'))
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
