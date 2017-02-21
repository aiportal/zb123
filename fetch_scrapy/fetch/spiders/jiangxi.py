import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodesExtractor, NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class JiangxiSpider(HtmlMetaSpider):
    name = 'jiangxi'
    alias = '江西'
    allowed_domains = ['jiangxi.gov.cn']
    start_referer = None
    start_urls = {
        '招标公告/采购公告': 'http://ggzy.jiangxi.gov.cn/jxzbw/zfcg/017002/017002001/MoreInfo.aspx?CategoryNum=017002001',
        '招标公告/变更公告': 'http://ggzy.jiangxi.gov.cn/jxzbw/zfcg/017002/017002002/MoreInfo.aspx?CategoryNum=017002002',
        '其他公告/答疑澄清': 'http://ggzy.jiangxi.gov.cn/jxzbw/zfcg/017002/017002003/MoreInfo.aspx?CategoryNum=017002003',
        '中标公告/结果公示': 'http://ggzy.jiangxi.gov.cn/jxzbw/zfcg/017002/017002004/MoreInfo.aspx?CategoryNum=017002004',
        '其他公告/单一来源': 'http://ggzy.jiangxi.gov.cn/jxzbw/zfcg/017002/017002005/MoreInfo.aspx?CategoryNum=017002005'
    }
    custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for subject, url in self.start_urls.items():
            yield scrapy.Request(url, meta={'params': {'subject': subject}}, dont_filter=True)

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='#MoreInfoList1_tdcontent table tr > td > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'area': './font//text()',
                                                    'start': '../../td[last()]//text()'})

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
        g['title'] = data.get('title') or data.get('text', '').strip('[]')
        g['area'] = self.join_words(self.alias, data.get('area'))
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('#TDContent > * > * > *:not(style)', '#TDContent > * > *'))
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
