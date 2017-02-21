import re
from datetime import datetime, date


class HtmlExtractor(object):
    def __init__(self, response):
        self.response = response

    # 使用css或xpath选择元素
    def select(self, css=None, xpath=None):
        return (css and self.response.css(css)) or (xpath and self.response.xpath(xpath)) or []

    # 提取文本内容
    def _text(self, selector, sep=''):
        ss = [s.strip() for s
              in selector.css('::text').extract()
              if s.strip()]
        return sep.join(ss).strip(sep)

    # 提取多行内容
    def _values(self, css=None, xpath=None, sep=''):
        return [self._text(r, sep) for r
                in self.select(css, xpath)
                if self._text(r, sep)]

    # 提取文本
    def text(self, css=None, xpath=None, sep=''):
        return sep.join(self._values(css, xpath))

    # 提取内容
    def contents(self, css=None, xpath=None, sep=''):
        return self._values(css, xpath, sep)

    # 提取日期
    def date(self, css=None, xpath=None):
        date_patterns = (
            {'pattern': r'(\d{4}-\d{1,2}-\d{1,2})', 'format': '%Y%m%d'},
            {'pattern': r'(\d{4}-\d{1,2}-\d{1,2})', 'format': '%Y-%m-%d'},
            {'pattern': r'(\d{4}年\d{1,2}月\d{1,2}日)', 'format': '%Y年%m月%d日'})
        text = self.text(css, xpath)
        for p in date_patterns:
            mc = text and re.search(p['pattern'], text)
            if mc:
                dt = datetime.strptime(mc.group(1), p['format'])
                return str(dt.date())

    # 提取脚本
    def script(self, pattern):
        scripts = self._values('script') or []
        for script in scripts:
            mc = re.search(pattern, script)
            if mc:
                return mc.group(1)

    def _extract(self, selector, css='::text', xpath=None, sep=''):
        """ 提取选中元素的或子元素的文本，不换行
        :param selector: 元素选择器
        :param css: 子元素选择器（默认为文本）
        :param xpath: 子元素选择器
        :param sep: 连接符
        :return:
        """
        if css:
            return sep.join([s.strip() for s in selector.css(css).extract() if s.strip()])
        elif xpath:
            return sep.join([s.strip() for s in selector.xpath(xpath).extract() if s.strip()])

    # 提取属性
    def subs(self, css=None, xpath=None, sub_css=(), sub_xpath=()):
        if sub_css:
            return [tuple([self._extract(o, css=s) for s in sub_css])
                    for o in self.select(css, xpath)]
        elif sub_xpath:
            return [tuple([self._extract(o, xpath=s) for s in sub_xpath])
                    for o in self.select(css, xpath)]


class RegexExtractor:
    @staticmethod
    def date(text):
        date_patterns = (
            {'pattern': r'(\d{4}-\d{1,2})', 'format': '%Y-%m'},
            {'pattern': r'(\d{1,2}-\d{1,2})', 'format': '%m-%d'},
            {'pattern': r'(\d{8})', 'format': '%Y%m%d'},
            {'pattern': r'(\d{4}-\d{1,2}-\d{1,2})', 'format': '%Y-%m-%d'},
            {'pattern': r'(\d{4}年\d{1,2}月\d{1,2}日)', 'format': '%Y年%m月%d日'})
        for p in date_patterns:
            mc = text and re.search(p['pattern'], text) or None
            if mc:
                dt = datetime.strptime(mc.group(1), p['format'])
                if dt.year < 1990:
                    dt = datetime(2016, dt.month, dt.day)
                return str(dt.date())
