import scrapy
from . import HtmlMetaSpider, GatherItem
from . import MetaLinkExtractor, DateExtractor, HtmlContentExtractor
import re


class NeimengguSpider(HtmlMetaSpider):
    name = 'neimenggu'
    alias = '内蒙古'
    allowed_domains = ["nmgp.gov.cn"]
    start_referer = 'http://www.nmgp.gov.cn/channel/zfcgw/col13923f.html'
    start_urls = ['http://www.nmgp.gov.cn/procurement/pages/tender.jsp?pos=1']
    start_params = {
        # 信息类型
        'type': {'0': '招标公告', '1': '更正公告/招标更正公告', '2': '中标公告', '3': '更正公告/中标更正公告', '4': '其他公告/废标公告',
                 '5': '其他公告/预审公告', '6': '其他公告/预审更正公告', '7': '其他公告/合同公告'},
        # 采购方式
        'purmet': {'1': '公开招标', '2': '邀请招标', '3': '竞争性谈判', '4': '询价', '5': '单一来源'},
    }
    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='body > table.recordlist tr > td > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'tags': '../font//text()',
                                                    'end': '../../td[contains(text(),"截止:")]/text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='div.pagenumber > a:contains(下一页)',
                                       url_attr='href', url_process=lambda x: x and 'tender.jsp'+x or None)

    def parse_item(self, response):
        """ 解析详情页
        """
        data = response.meta['data']
        tags = 'tags' in data and data['tags'].strip('[]').split('|') or []

        # GatherItem
        g = self.gather_item(response)

        g['day'] = re.sub('.*/(\d{4})/(\d{1,2})/(\d{1,2})/.*', '\g<1>-\g<2>-\g<3>', response.url)
        g['end'] = DateExtractor.extract(data.get('end'))
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias, tags and tags[0] or None)
        g['subject'] = self.join_words(data.get('type'), data.get('purmet'))
        g['industry'] = tags[1:] and tags[1] or None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='#wrapper > table td > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)
        yield g
