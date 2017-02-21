import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, FileLinkExtractor, DateExtractor, HtmlContentExtractor
import re


# W005_001: 需求公示（需求征求意见、供应商意见、采购人回复）
# W001_001: 采购信息（公开招标、竞争性谈判、邀请招标、单一来源、询价采购、竞争性磋商）
# W004_004: 更正公告（公开招标、竞争性谈判、邀请招标、单一来源、询价采购、竞争性磋商）
# W004_001: 结果公告（公开招标、竞争性谈判、邀请招标、单一来源、询价采购、竞争性磋商）


class TianjinSpider(HtmlMetaSpider):
    name = 'tianjin'
    alias = '天津'
    allowed_domains = ["tjgpc.gov.cn"]
    start_referer = None
    start_urls = ['http://www.tjgpc.gov.cn/webInfo/getWebInfoListForwebInfoClass.do']
    start_params = {
        'fkWebInfoclassId': {'W005_001': '预公告/需求公示',
                             'W001_001': '招标公告/采购信息',
                             'W004_004': '更正公告',
                             'W004_001': '中标公告/结果公告'},
        'page': {'1': None},
        'pagesize': {'10': None}
    }
    # 提取详情页链接
    link_extractor = MetaLinkExtractor(css='div.cur > table tr', url_attr='href', attrs_xpath={
        'tags': './/a[1]/text()', 'href': './/a[2]/@href', 'title': './/a[2]/@title', 'text': './/a[2]/text()',
        'start': './td[last()]/text()'
    })
    # 提取翻页链接
    page_extractor = NodeValueExtractor(css='div.pager_btns > a.active:contains(下一页)', value_xpath='./@onclick',
                                        value_process=lambda x: re.search('(\d+)', x).group(1))

    def page_requests(self, response):
        next_page = [p for p in self.page_extractor.extract_values(response)]
        if next_page:
            url = self.replace_url_param(response.request.url, page=next_page[0])
            yield scrapy.Request(url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        tags = 'tags' in data and data['tags'].strip('[]').split('|') or []

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('fkWebInfoclassId'), tags and tags[0] or None)
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='div.xx_right table tr:nth-of-type(3) > td > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = (lambda x: x and x.group(1))(re.search('（.*(TGPC-.*)）', g['title']))
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)
        yield g
