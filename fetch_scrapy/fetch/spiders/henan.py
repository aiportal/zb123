import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
from urllib.parse import urljoin
import re


class HenanSpider(HtmlMetaSpider):
    name = 'henan'
    alias = '河南'
    allowed_domains = ["hngp.gov.cn"]
    start_referer = None
    start_urls = ['http://www.hngp.gov.cn/henan/ggcx']
    start_params = {
        'appCode': {'H60': None},
        'channelCode': {'0101': '招标公告', '0102': '中标公告/结果公告', '0103': '更正公告/变更公告',
                        '1201': '其他公告/网上竞价', '1202': '中标公告/竞价结果',
                        '1301': '其他公告/单一来源', '1302': '其他公告/进口产品', '1303': '其他公告/技术指标', '1304': '其他公告/其他',
                        # '1401': '合同公告', '1402': '验收结果公告'
        },
        # 'bz': {'1': '省级', '0': '市县'},
        'bz': {'2': None},
        'pageSize': {'10': None},
    }
    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='.List2 > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span/text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='div.PageList > ul > li.nextPage a', url_attr='href')

    def parse_item(self, response):
        """ 获取详情页内容 """
        self.logger.info(response.url)
        script = NodeValueExtractor.extract_text(response.css('script:contains("jQuery(document).ready") ::text'))
        if script:
            base_url = response.url.rpartition('/')[0] + '/'
            href = re.search('\$\.get\(\"([/\w\.]+)', script).group(1)
            url = urljoin(base_url, href)
            response.meta['top_url'] = response.url
            return scrapy.Request(url, meta=response.meta, callback=self.parse_detail)
            # 'http://www.hngp.gov.cn/webfile/henan/cgxx/cggg/webinfo/2016/11/15/1479176400050699.htm'

    def parse_detail(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('channelCode'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='body > *')
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
