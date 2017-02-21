import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, FileLinkExtractor, DateExtractor, HtmlContentExtractor
import re


# 'http://www.bjcz.gov.cn/zfcg/cggg/syzbgg/index.htm',    # 招标公告
# 'http://www.bjcz.gov.cn/zfcg/cggg/syzgysgg/index.htm',  # 资格预审公告
# 'http://www.bjcz.gov.cn/zfcg/cggg/sycjjggg/index.htm',  # 中标成交公告
# 'http://www.bjcz.gov.cn/zfcg/cggg/sycghtgg/index.htm',  # 采购合同公告
# 'http://www.bjcz.gov.cn/zfcg/cggg/sydylygs/index.htm',  # 单一来源公示
# 'http://www.bjcz.gov.cn/zfcg/cggg/syqtgg/index.htm',    # 其他公告


class TianjinSpider(HtmlMetaSpider):
    name = 'beijing'
    alias = '北京'
    allowed_domains = ["bjcz.gov.cn"]
    start_pages = [
        ('http://www.bjcz.gov.cn/zfcg/cggg/{0}/index.htm'.format(k), {'subject': v}) for k, v in
        {
            'zbgg': '招标公告',
            'zbcjgg': '中标公告/中标成交',
            'zgysgg': '其他公告/资格预审',
            'cghtgg': '其他公告/采购合同',
            'dylygs': '其他公告/单一来源',
            'qtgg': '其他公告'
        }.items()
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.0}

    def start_requests(self):
        for url, data in self.start_pages:
            yield scrapy.Request(url, meta={'params': data}, dont_filter=True)

    # 提取详情页链接
    def link_requests(self, response):
        base_url = re.sub('index\.htm$', '', response.url)
        count = len(response.css('#DocumentsDataSrc d > t'))    # 节点总数
        link_regex = re.compile('\[CDATA\[.*<a href=\"\./(\w+\.htm)\"(.*)\]\]>.*\s+(.*)')
        nodes = link_regex.findall(response.text)
        for url, title, day in nodes:
            if not url:
                continue
            url = base_url + url.lstrip('./')
            title = (lambda x: x and x.group(1))(re.search('>(.+)<', title))
            day = DateExtractor.extract(day)
            data = response.meta.get('params', {})
            data.update(title=title, day=day)
            yield scrapy.Request(url, meta={'data': data})
            count -= 1
        if count > 0:
            raise ValueError('parse beijing index error: ' + response.url)

    def page_requests(self, response):
        return []

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        title = NodeValueExtractor.extract_text(response.css('#titlezoom::text'))
        day = NodeValueExtractor.extract_text(response.css('#zoom').xpath('./p[1]/text()'))
        tags = [s.strip() for s in NodeValueExtractor.extract_text(response.css('div.zj_wz::text')).split('->')]
        g['day'] = data.get('start') or DateExtractor.extract(day)
        g['end'] = None
        g['title'] = data.get('title') or title
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'), *(tags and tags[-2:] or []))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='#zoom > div > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)
        yield g
