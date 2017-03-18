# -*- coding: utf-8 -*-
import scrapy
import re
from datetime import datetime, date
from urllib.parse import urljoin
import json
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit
from scrapy.selector import Selector
from typing import List, Union


class NodesExtractor:
    """ 从索引页中提取带有元数据的链接 """
    def __init__(self, css=(), xpath=(), attrs_css: dict=None, attrs_xpath: dict=None):
        self.css = isinstance(css, str) and (css,) or css
        self.xpath = isinstance(xpath, str) and (xpath,) or xpath
        self.attrs_css = attrs_css or {}
        self.attrs_xpath = attrs_xpath or {}

    @staticmethod
    def extract_text(selector):
        """ 提取节点的文本内容 """
        return ''.join([s.strip() for s in selector.extract() if s.strip()])

    def _extract_nodes(self, response):
        """ 将节点集合提取为多个字典对象 """
        selectors = []
        for css in self.css:
            selectors += response.css(css)
        for xpath in self.xpath:
            selectors += response.xpath(xpath)
        return [self._extract_node(o) for o in selectors]

    def _extract_node(self, selector):
        """ 将节点提取为字典对象 """
        node = selector.root.attrib or {}
        for k, v in self.attrs_css.items():
            node[k] = self.extract_text(selector.css(v))
        for k, v in self.attrs_xpath.items():
            node[k] = self.extract_text(selector.xpath(v))
        return node

    def extract_nodes(self, response):
        """ 将节点集合提取为多个字典对象 """
        return self._extract_nodes(response)


class NodeValueExtractor(NodesExtractor):
    """ 提取字符串数组 """
    def __init__(self, css=(), xpath=(), value_css=None, value_xpath=None, value_process=lambda x: x, value_regex=None):
        attrs_css = value_css and {'value': value_css} or {}
        attrs_xpath = value_xpath and {'value': value_xpath} or {}
        super().__init__(css=css, xpath=xpath, attrs_css=attrs_css, attrs_xpath=attrs_xpath)
        self.value_process = value_process
        self.value_regex = value_regex

    def extract_values(self, response):
        """ 将多个节点的内容提取为文本列表 """
        return [self.value_process(n.get('value')) for n in self._extract_nodes(response) if n]
        # TODO: [self.value_process(n.get('value')) for n in self._extract_nodes(response) if n and n.get('value')]
        # TODO: process values by value_regex

    def extract_value(self, response):
        values = [self.value_process(n.get('value')) for n in self._extract_nodes(response) if n and n.get('value')]
        if self.value_regex:
            values = [re.search(self.value_regex, v).groups() for v in values if re.search(self.value_regex, v)]
            values = [len(v) > 1 and v or v[0] for v in values]     # 如果只有一个值，去掉元组包装
        return values and values[0] or None


class MetaLinkExtractor(NodesExtractor):
    """ 提取带元数据的链接 """
    class MetaLink:
        def __init__(self, node, url):
            self.url = url
            self.meta = node

    def __init__(self, css=(), xpath=(), attrs_css: dict=None, attrs_xpath: dict=None,
                 url_attr='href', url_process=lambda x: x):
        super().__init__(css=css, xpath=xpath, attrs_css=attrs_css, attrs_xpath=attrs_xpath)
        self.url_attr = url_attr
        self.url_process = url_process

    def extract_links(self, response):
        base_url = response.url.rpartition('/')[0] + '/'
        for node in self._extract_nodes(response):
            attr = node.get(self.url_attr)
            value = self.url_process(attr)
            if value:
                url = value.startswith('http') and value or urljoin(base_url, value)
                yield self.MetaLink(node, url)


class FileLinkExtractor(MetaLinkExtractor):
    """ 提取附件链接
    """
    def extract_files(self, response):
        return [{'url': f.url, 'text': f.meta['text'], 'file': None}
                for f in self.extract_links(response)]


class JsonLinkGenerator:
    class JsonLink:
        def __init__(self, data, url, ref_url, index_url):
            self.data = data
            self.url = url
            self.ref_url = ref_url
            self.index_url = index_url

    def __init__(self, url_format: str, ref_format: str, values_extractor=lambda x: []):
        """ 基于JSON数据构造详情页链接
        :param url_format: 详情页请求网址
        :param ref_format: 详情页框架网址
        :param values_extractor: 获取数据节点列表
        :return: JsonLink
        """
        self.url_format = url_format
        self.ref_format = ref_format or ''
        self.values_extractor = values_extractor

    def generate_links(self, response):
        base_url = response.url.rpartition('/')[0] + '/'
        res = json.loads(response.text)
        for v in self.values_extractor(res):
            url = self.url_format.format(v)
            ref = self.ref_format.format(v)
            url = urlsplit(url).scheme and url or urljoin(base_url, url)
            ref = urlsplit(ref).scheme and ref or (ref and urljoin(base_url, ref) or None)
            if url:
                yield JsonLinkGenerator.JsonLink(v, url, ref, response.url)


class JsonPageGenerator:
    def __init__(self, page_parameter, rows_parameter, total_extractor=lambda x: 0):
        """ 基于JSON数据构建翻页链接
        :param page_parameter: 页码参数名称
        :param rows_parameter: 每页行数的参数名称
        :param total_extractor: 从JSON对象中获取总行数
        :return: 下一页的url
        """
        self.page_parameter = page_parameter
        self.rows_parameter = rows_parameter
        self.total_extractor = total_extractor

    def generate_page(self, response):
        url = response.request.url
        params = parse_qs(urlsplit(url).query)
        page = int(params[self.page_parameter][0])
        rows = int(params[self.rows_parameter][0])
        res = json.loads(response.text)
        total = self.total_extractor(res)
        if (page * rows) < total:
            return self._replace_url_param(url, self.page_parameter, page + 1)

    @staticmethod
    def _replace_url_param(url, key, value):
        scheme, netloc, path, query, fragment = urlsplit(url)
        params = parse_qs(query)
        params[key] = str(value)
        query = urlencode(params, True)
        return urlunsplit((scheme, netloc, path, query, fragment))


class HtmlContentExtractor(object):
    """ 提取正文内容"""
    # TODO: 如果给出多个选择器，至少应保证有内存
    def __init__(self, css=(), xpath=()):
        """ 多个selector是并行择一关系，最终仅使用其中一条
        如果有一个css/xpath选中了多条记录，就使用这个css/xpath
        如果没有选中多条记录，就层层递进地往下延伸，直到有多条记录被选中
        """
        self.css = isinstance(css, str) and (css,) or css
        self.xpath = isinstance(xpath, str) and (xpath,) or xpath

    def _select_list(self, response):
        selectors = [response.css(x) for x in self.css] + [response.xpath(x) for x in self.xpath]
        # while not any(len(x) > 1 for x in selectors):
        #     selectors = [x.xpath('./*') for x in selectors
        #                  if not any(s for s in x.xpath('./text()').extract() if s.strip())]
        return next((x for x in selectors if len(x) > 1), next(iter(selectors), []))

    def extract_contents(self, response):
        selectors = self._select_list(response)
        rows = list(map(lambda x: x.root.tag in ['table'] and x.extract() or x.xpath('.//text()').extract(), selectors))
        return [''.join(s.strip() for s in x) for x in rows if any(s.strip() for s in x)]

    def extract_digest(self, response, key_max_len=30, val_max_len=100):
        selectors = self._select(response)
        while selectors and len(selectors) < 2:
            selectors = [s for s in selectors[0].xpath('./*')]
        contents = [self._text(s) for s in selectors]
        rows = [tuple(s.split('：')[-2:]) for s in contents if '：' in s]
        return dict(x for x in rows if len(x) == 2 and len(x[0]) < key_max_len and len(x[1]) < val_max_len)

    def _select(self, response):
        selectors = []
        for css in self.css:
            selectors += response.css(css)
        for xpath in self.xpath:
            selectors += response.xpath(xpath)
        return selectors

    @staticmethod
    def _text(selector, sep=''):
        return sep.join([s.strip() for s in selector.xpath('.//text()').extract() if s.strip()])


class HtmlPlainExtractor:
    """ 将HTML文件转换为普通文本 """
    def __init__(self, css=(), xpath=(), tags=('div', 'p', 'ul', 'table')):
        """ 多个选择器为择一使用关系，优先使用选中元素最多的那个 """
        self.css = isinstance(css, str) and (css,) or css
        self.xpath = isinstance(xpath, str) and (xpath,) or xpath
        self.tags = tags

    def contents(self, response):
        selectors = [response.css(x) for x in self.css] + [response.xpath(x) for x in self.xpath]
        selector = max(selectors, key=lambda x: len(x))
        if not selector:
            return []

        contents = []
        for row in selector:
            assert isinstance(row, scrapy.Selector)
            tag = hasattr(row.root, 'tag') and row.root.tag.lower() or 'str'

            if tag == 'str':
                content = ''.join([s.strip() for s in row.extract() if s.strip()])
            elif tag in ('table', 'img'):
                content = ''.join([s for s in row.extract() if s])
            elif tag in ('div', 'p', 'tr', 'span', 'u', 'h1', 'font'):
                lns = [x for x in row.xpath('.//text()').extract()]
                content = ''.join([s.strip() for s in lns if s.strip()])
            elif tag in ('style', 'script'):
                content = ''
            else:
                lns = [x for x in row.xpath('.//text()').extract()]
                content = ''.join([s.strip() for s in lns if s.strip()])

            if content:
                assert isinstance(content, str)
                contents.append(content)
        return contents

    @staticmethod
    def digest(contents: list, key_max_len=30, val_max_len=255):
        """ 提取摘要信息 """
        digest = {}
        for i, row in enumerate(contents):
            if '：' in row.strip('：'):
                val = row.split('：')[-2:]
                if len(val) == 2 and len(val[0]) < key_max_len and len(val[1]) < val_max_len:
                    digest[val[0]] = val[1]
            elif row.endswith('：'):
                if i + 1 >= len(contents):
                    continue
                if len(row) < key_max_len and len(contents[i+1]) < val_max_len:
                    digest[row] = contents[i+1]
        return digest


class DateExtractor:
    """ 从字符串中提取日期
    """
    patterns = [
        {'regex': r'(\d{4}-\d{1,2}-\d{1,2})', 'format': '%Y-%m-%d'},
        {'regex': r'(\d{4}年\d{1,2}月\d{1,2}日)', 'format': '%Y年%m月%d日'},
        {'regex': r'(\d{8})', 'format': '%Y%m%d'},
        {'regex': r'(\d{4}-\d{1,2})', 'format': '%Y-%m'},
        {'regex': r'(\d{1,2}-\d{1,2})', 'format': '%m-%d'},
    ]

    @staticmethod
    def extract(text: str, default: date=date.min, max_day: Union[date, None]=date.today()) -> str:
        """ 从字符串中提取日期 """
        if not text:
            return str(default)

        pattern = next((p for p in DateExtractor.patterns if re.search(p['regex'], text)), None)
        if not pattern:
            return str(default)

        mc = re.search(pattern['regex'], text)
        dt = datetime.strptime(mc.group(1), pattern['format']).date()
        if dt.year < 1990:
            dt = date(date.today().year, dt.month, dt.day)
        if max_day and max_day < dt:
            dt = max_day
        return str(dt)


# class ContentExtractor:
#     """ 从HTML中提取正文内容
#     """
#     def __init__(self, response):
#         self.response = response
#
#     def extract(self, css=None, xpath=None, sep=''):
#         selectors = (css and self.response.css(css)) or (xpath and self.response.xpath(xpath)) or []
#         if not selectors:
#             return None
#         return [self._text(o, sep) for o in selectors if self._text(o, sep)]
#
#     # 提取文本内容
#     def _text(self, selector, sep=''):
#         ss = [s.strip() for s
#               in selector.css('::text').extract()
#               if s.strip()]
#         return sep.join(ss).strip(sep)


class ScriptExtractor:
    """ 从HTML中提取脚本内容
    """
    def __init__(self, response):
        self.response = response

    def extract(self):
        return None
