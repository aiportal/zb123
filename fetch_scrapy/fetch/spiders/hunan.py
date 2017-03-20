import scrapy
from . import JsonMetaSpider
from . import DateExtractor, HtmlPlainExtractor, MoneyExtractor
import json
import re


class HunanSpider(JsonMetaSpider):
    name = 'hunan'
    alias = '湖南'
    allowed_domains = None      # ['ccgp-shandong.gov.cn', 'ccgp-shandong.gov.cn:8080']
    start_referer = None        # 'http://www.ccgp-hunan.gov.cn:8080/page/notice/more.jsp'
    start_urls = [
        'http://www.ccgp-hunan.gov.cn:8080/mvc/getNoticeList4Web.do',           # 省级
        'http://www.ccgp-hunan.gov.cn:8080/mvc/getNoticeListOfCityCounty.do'    # 市县
    ]
    start_params = {
        'page': '1',
        'pageSize': '50'
    }
    custom_settings = {
        'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 1.8,
        'DOWNLOADER_MIDDLEWARES': {
            'fetch.middlewares.EmptyRetryMiddleware': None,
            'fetch.middlewares.HttpExceptionMiddleware': 300,
        }
    }

    def start_requests(self):
        meta = {'params': self.start_params}
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        yield scrapy.FormRequest(self.start_urls[0], formdata=self.start_params, meta=meta, headers=headers)
        meta.update(area_id='1')
        yield scrapy.FormRequest(self.start_urls[1], formdata=self.start_params, meta=meta, headers=headers)

    def link_requests(self, response):
        url_ref = 'http://www.ccgp-hunan.gov.cn:8080/page/notice/notice.jsp?noticeId={0}'
        url_item = 'http://www.ccgp-hunan.gov.cn:8080/mvc/viewNoticeContent.do?noticeId={0}&area_id={1}'
        data = json.loads(response.text)
        for row in isinstance(data, list) and data or data['rows']:
            ref = url_ref.format(row['NOTICE_ID'])
            url = url_item.format(row['NOTICE_ID'], response.meta.get('area_id', ''))
            meta = {'data': row, 'top_url': ref, 'index_url': response.url}
            yield scrapy.Request(url, meta=meta, headers={'Referer': ref}, callback=self.parse_item)

    def page_requests(self, response):
        params = response.meta['params']
        page = int(params['page'])
        size = int(params['pageSize'])

        data = json.loads(response.text)
        if isinstance(data, list):
            if len(data) == size:
                params['page'] = str(page + 1)
                yield scrapy.FormRequest(response.url, formdata=params, meta={'params': params})
        else:
            total = json.loads(response.text)['total']
            if (page * size) < total:
                params['page'] = str(page + 1)
                yield scrapy.FormRequest(response.url, formdata=params, meta={'params': params})

    def parse_item(self, response):
        # 返回空值时，换area_id重试
        if len(response.body) == 0:
            url = response.url.endswith('=1') and response.url.rstrip('1') or (response.url + '1')
            if not self.url_exists(url):
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        """ 解析详情页 """
        data = response.meta['data']
        # 'AREA_ID'  = {int} -1
        # 'AREA_NAME'  = {str} '湖南省'
        # 'DEPT_ID'  = {NoneType} None
        # 'NEWWORK_DATE'  = {str} '2016-12-02'
        # 'NEWWORK_DATE_ALL'  = {dict} {...}
        # 'NOTICE_CATEGORY_CODE'  = {str} '01'
        # 'NOTICE_ID'  = {int} 29576
        # 'NOTICE_NAME'  = {str} '单一来源公示'
        # 'NOTICE_TITLE'  = {str} '湖南省防汛抗旱指挥部办公室喷水组合式防汛抢险舟采购单一来源采购公示'
        # 'NOTICE_TYPE_NAME'  = {str} '单一来源公告'
        # 'ORG_CODE'  = {str} '25217'
        # 'PRCM_MODE_CODE'  = {str} '05'
        # 'PRCM_MODE_CODE1'  = {NoneType} None
        # 'PRCM_MODE_NAME'  = {str} '单一来源'
        # 'PRCM_PLAN_ID'  = {NoneType} None
        # 'PRCM_PLAN_NO'  = {NoneType} None
        # 'RN'  = {int} 1
        # 'page'  = {int} 1
        # 'pageSize'  = {int} 50

        # 详情页正文
        content_extractor = HtmlPlainExtractor(
            xpath=('//body/div/p | //body/div/table', '//body/div/div/p | //body/div/div/table',
                   '//form/div/table',  # '//form/div/table/tr/td/*',
                   '//body/table/tr',
                   '//body/div/div/div/p',
                   '//body/div/p|//body/div/div/img',
                   '//body/*'))
        contents = content_extractor.contents(response)
        digest = content_extractor.digest(contents)

        link = digest.get('公告链接')
        if link:
            assert len(contents) < 10
            url = link.startswith('http:') and link or ('http://'+link)
            if not self.url_exists(url):
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('NEWWORK_DATE'))
        g['end'] = None
        g['title'] = data.get('NOTICE_TITLE')
        g['area'] = self.join_words(self.alias, data.get('AREA_NAME'))
        g['subject'] = self._subjects(data)
        g['industry'] = None

        g['contents'] = contents
        g['pid'] = None
        g['tender'] = None
        g['budget'] = MoneyExtractor.money_max(response.xpath('//body'))
        g['tels'] = None
        g['extends'] = data
        g['digest'] = digest

        yield g

    def _subjects(self, data: dict):
        subject = {
            '采购公告': '招标公告',
            '更正公告': '更正公告',
            '成交公告': '中标公告',
            '合同公告': '其他公告',
            '单一来源公示': '其他公告',
        }.get(data['NOTICE_NAME'], '其他公告')
        return self.join_words(subject, data.get('NOTICE_NAME'), data.get('PRCM_MODE_NAME'))

    # def _budget(self, digest, contents):
    #     tags = ['采购预算', '项目预算', '预算', '合同金额', '金额']
    #     patterns_yuan = ['([\d,]+)\.\d{1,2}\s*元?', '￥?\s*([\d,]+)\s*元']
    #     patterns_wan = ['￥?\s*([\d,.]+)\s*万元?']
    #
    #     # 废标公告直接返回0
    #     if any(['废标原因' in x for x in digest.keys()]):
    #         return 0
    #
    #     # 在摘要信息中搜索包含tags内容的关键词，提取后面的金额
    #     items = [(x, digest[x]) for x in digest.keys() if any([s in x for s in tags])]
    #     if len(items) > 1:
    #         self.logger.error('budget: ' + str(items))
    #     for k, v in items:
    #         values_yuan = [int(re.search(p, v).group(1).replace(',', ''))
    #                        for p in patterns_yuan if re.search(p, v)]
    #         values_wan = [int(float(re.search(p, v).group(1).replace(',', '')) * 10000)
    #                       for p in patterns_wan if re.search(p, v)]
    #         if any(values_yuan + values_wan):
    #             return max(values_yuan + values_wan)
    #
    #     # 在表格中搜索包含tags内容的关键词，提取同行或合并同列的金额
    #
    #     # 遍历所有行，搜索表示金额的内容，提取最大值
    #     money_list = []
    #     lns = [s for s in contents if any([re.search(p, s) for p in (patterns_yuan + patterns_wan)])]
    #     for ln in lns:
    #         for p in patterns_yuan:
    #             vs = [int(s.replace(',', '')) for s in re.findall(p, ln) if s]
    #             money_list.extend(vs)
    #         for p in patterns_wan:
    #             vs = [int(float(s.replace(',', '')) * 10000) for s in re.findall(p, ln) if s]
    #             money_list.extend(vs)
    #     if money_list:
    #         return max(money_list)
    #     else:
    #         return None


# class HtmlDigestExtractor:
#     key_max_len = 30
#     val_max_len = 255
#
#     def __init__(self, css: tuple=(), xpath: tuple=(), tags: tuple=()):
#         self.css = css
#         self.xpath = xpath
#         self.tags = tags
#         setattr(scrapy.Selector, 'content', lambda x: ''.join([s.strip() for s in x.extract() if s.strip()]))
#
#     def contents(self, response):
#         selectors = [response.css(x) for x in self.css] + [response.xpath(x) for x in self.xpath]
#         selector = max(selectors, key=lambda x: len(x))
#         assert isinstance(selector, scrapy.selector.SelectorList)
#         if not selector:
#             return None
#
#         return self._extract_contents(selector)
#
#     def _extract_contents(self, selector):
#         """ 提取多行内容 """
#         contents = []
#         for row in selector:
#             assert isinstance(row, scrapy.Selector)
#
#             # 文本元素
#             if not hasattr(row.root, 'tag'):
#                 text = self.text(row)
#                 if text:
#                     contents.append(text)
#                 continue
#
#             # 表格元素
#             tag = row.root.tag
#             if tag == 'table':
#                 if row.xpath('.//table'):   # 包含子表的，按行提取
#                     lns = self._extract_contents(row.xpath('./tr|./thead/tr|.tbody/tr'))
#                     contents.extend(lns)
#                 else:
#                     lns = self._extract_table(row)
#                     contents.extend(lns)
#                 continue
#
#             # 块元素
#             if row.xpath('.//table'):   # 包含字表的，递归提取
#                 lns = self._extract_contents(row.xpath('./*'))
#                 contents.extend(lns)
#             else:
#                 lns = self._extract_block(row)
#                 contents.extend(lns)
#
#         return contents
#
#     def _extract_block(self, selector: scrapy.Selector):
#         """ 提取块元素内容 """
#         assert hasattr(selector.root, 'tag') and selector.root.tag != 'table'
#         assert not selector.xpath('.//table')
#         tag = selector.root.tag
#
#         contents = []
#         if tag in ('div', 'p'):
#             text = self.text(selector.xpath('.//text()'))
#             if text:
#                 contents.append(text)
#         elif tag == 'ul':
#             lns = [self.text(x) for x in selector.xpath('./li//text()')]
#             contents.extend([s for s in lns if s])
#         else:
#             lns = [self.text(x) for x in selector.xpath('.//text()')]
#             contents.extend([s for s in lns if s])
#
#         return contents
#
#     def _extract_table(self, selector: scrapy.Selector):
#         """ 提取表格内容 """
#         assert hasattr(selector.root, 'tag') and selector.root.tag == 'table'
#         assert not selector.xpath('.//table')
#         return []
#
#     def digest(self, response):
#         contents = self.contents(response)
#         lines = [isinstance(x, str) and x or '' for x in contents]
#         tables = [x for x in contents if not isinstance(x, str)]
#
#         # 遍历文本内容，提取冒号分隔的关键词摘要
#         digest = []
#         for i, ln in enumerate(lines):
#             if '：' in ln.strip('：'):
#                 assert len(ln.split('：')) > 1
#                 k, v = ln.split('：')[-2:]
#                 if len(k) < self.key_max_len and len(v) < self.val_max_len:
#                     digest.append((k,v))
#             elif ln.endswith('：') and len(ln) < self.key_max_len:
#                 if (i + 1) < len(contents) and len(contents[i+1]) < self.val_max_len:
#                     digest.append((ln, contents[i+1]))
#
#         # 遍历表格内容，按列提取关键词摘要
#         return digest
#
#     @staticmethod
#     def text(selector: scrapy.Selector):
#         return ''.join([s.strip() for s in selector.extract() if s.strip()])
#
#
# class HtmlTable:
#     __slots__ = ['source', 'grid']
#
#     def __init__(self, source: str, grid: List[list]):
#         self.source = source
#         self.grid = grid
#
#     @staticmethod
#     def create(selector: scrapy.Selector):
#         assert hasattr(selector.root, 'tag') and selector.root.tag.lower() == 'table'
#         assert not selector.xpath('.//table')
#
#         rows = selector.xpath('./tr|./thead/tr|./tbody/tr')
#         grid = [[] for _ in rows]
#         for i, tr in enumerate(rows):
#             for j, td in enumerate(tr.xpath('./td')):
#                 rowspan = td.root.attrib.get('rowspan', 1)
#                 colspan = td.root.attrib.get('colspan', 1)
#                 text = ''.join([s.strip() for s in td.xpath('.//text()').extract() if s.strip()])
#
#                 cell = HtmlTable.Cell(text, rowspan, colspan)
#                 for k in range(0, rowspan):
#                     grid[i + k].append(cell)
#                 for k in range(0, colspan):
#                     grid[i].append(cell)
#
#         return HtmlTable(selector.extract(), grid)
#
#     def __str__(self):
#         return self.source
#
#     class Cell:
#         __slots__ = ['rowspan', 'colspan', 'value']
#
#         def __init__(self, value: str, rowspan: int=1, colspan: int=1):
#             self.value = value
#             self.rowspan = rowspan
#             self.colspan = colspan
#
#         def __str__(self):
#             return self.value
