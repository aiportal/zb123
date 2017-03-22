import scrapy
from .. import HtmlMetaSpider
from fetch.extractors import NodeValueExtractor, MetaLinkExtractor, FileLinkExtractor, DateExtractor, HtmlContentExtractor
from fetch.items import GatherItem
import re


# channelCode:0005（采购公告）000501：公开招标，000502：邀请招标...
# channelCode:0006（更正公告）
# channelCode:0008（中标公告）
# channelCode:0014（代理机构公示）
# channelCode:0017（电子反拍公告）
# channelCode:-3（批量集中采购）


class GuangdongSpider(HtmlMetaSpider):
    name = 'guangdong'
    alias = '广东'
    allowed_domains = ['gdgpo.gov.cn']
    start_urls = ['http://www.gdgpo.gov.cn/queryMoreInfoList.do']
    start_params = {
        'channelCode': {
            '0005': '招标公告/采购公告',
            '0006': '更正公告',
            '0008': '中标公告',
        },
        'pageIndex': 1,
        'pageSize': 50
    }

    def start_requests(self):
        for k, v in self.start_params['channelCode'].items():
            params = {'channelCode': k, 'pageIndex': '1', 'pageSize': '50'}
            yield scrapy.FormRequest(self.start_urls[0], formdata=params, meta={'params': params}, dont_filter=True)

    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='div.n_main div.m_m_cont > ul.m_m_c_list > li', url_attr='href',
                                       attrs_xpath={'href': './a/@href', 'title': './a/@title', 'text': 'a//text()',
                                                    'day': 'em//text()', 'tags': 'span//text()'})
    # 索引页翻页链接
    page_extractor = NodeValueExtractor(css='div.n_main div.m_m_cont > div.m_m_c_page a:contains(下一页)',
                                        value_xpath='./@href',
                                        value_process=lambda x: re.sub('.*\((\d+)\).*', '\g<1>', x))

    def page_requests(self, response):
        next_page = [p for p in self.page_extractor.extract_values(response)]
        if next_page:
            params = response.meta['params']
            params['pageIndex'] = next_page[0]
            yield scrapy.FormRequest(response.url, formdata=params, meta={'params': params})

    # 详情页摘要信息
    digest_extractor = NodeValueExtractor(css='div.zw_c_c_qx span', value_xpath='.//text()',
                                          value_process=lambda x: tuple(s.strip()
                                                                        for s in x.split('：')[-2:]
                                                                        if s))
    # 详情页正文
    content_extractor = HtmlContentExtractor(css='div.zw_c_c_cont > *')
    # 附件下载链接
    files_extractor = FileLinkExtractor(css='div.zw_c_c_cont a', attrs_xpath={'text': './/text()'},
                                        url_process=lambda x: re.search('/upload/files/', x or '') and x or None)

    def parse_item(self, response):
        """ 解析详情页
        """
        data = response.meta['data']
        digest = dict([x for x in self.digest_extractor.extract_values(response) if len(x) == 2])
        # digest = dict(self.digest_extractor.extract_values(response))
        # digest = self.parse_digest(response.css('div.zw_c_c_qx span'))
        # '代理机构' = '深圳市国际招标有限公司'
        # '信息来源' = '广东省政府采购网'
        # '发布日期' = '2016-09-30 12:05:10'
        # '发布机构' = '深圳市国际招标有限公司'
        # '采购品目' = '检察诉讼设备'
        # '采购项目编号' = '440000-201609-148015-0051'
        # '项目经办人' = '潘劭熙'
        # '项目负责人' = '郑建兵'
        # '预算金额' = '298,000.00\r\n\t\t\t\t\t\t\t元'

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('day'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        tags = [s.strip() for s in data['tags'].strip('[]').split('·')]
        area = tags and tags[-1:][0]
        subject = len(tags) > 1 and '/'.join(tags[:-1]) or None
        g['area'] = self.join_words(self.alias, area)
        g['subject'] = self.join_words(data.get('channelCode'), subject)
        g['industry'] = digest.get('采购品目')

        g['contents'] = self.content_extractor.extract_contents(response)
        g['pid'] = digest.get('采购项目编号')
        g['tender'] = None
        g['budget'] = digest.get('预算金额')
        g['tels'] = None
        g['extends'] = data
        g['digest'] = dict(self.content_extractor.extract_digest(response), **digest)

        yield g
