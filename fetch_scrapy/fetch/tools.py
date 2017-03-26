import scrapy
from database import JobIndex
import urllib.parse as parse
import itertools
from typing import Iterable, Tuple, Union, List
import re


class SpiderTool:
    """ 通用工具类 """

    @classmethod
    def url_exists(cls, url) -> bool:
        """ url 是否存在 """
        return JobIndex.url_exists(url)

    @classmethod
    def url_filter(cls, links: iter, key: callable=lambda x: x) -> list:
        """ 批量过滤已存在的 url """
        return [x for x in links if not cls.url_exists(key(x))]

    @staticmethod
    def url_replace(url, **kwargs) -> str:
        """ 替换url中的参数 """
        scheme, netloc, path, query, fragment = parse.urlsplit(url)
        params = parse.parse_qs(query)
        for k, v in sorted(kwargs.items()):
            params[k] = str(v)
        query = parse.urlencode(params, True)
        return parse.urlunsplit((scheme, netloc, path, query, fragment))

    @staticmethod
    def iter_params(params: dict) -> Iterable[Tuple[dict, dict]]:
        """ 遍历参数组合 """
        params = {k: isinstance(v, dict) and v or {str(v): None} for k, v in params.items()}
        params = [list(zip(itertools.repeat(k), v.items())) for k, v in params.items()]
        for param in [list(i) for i in itertools.product(*params)]:
            form = {}
            meta = {}
            for k, (v, m) in param:     # key, value, meta in param
                form[k] = v
                meta[k] = m or v
            yield form, meta

    @staticmethod
    def re_nums(regex: str, text: str) -> Union[int, List[int]]:
        """ 正则提取数字 """
        r = re.compile(regex)
        assert r.groups > 0
        mcs = r.findall(text)
        if r.groups > 1:
            return mcs and [int(x) for x in mcs[0]] or list(itertools.repeat(0, r.groups))
        else:
            return mcs and int(mcs[0]) or 0

    @staticmethod
    def re_text(regex: str, text: str) -> Union[str, List[str]]:
        """ 正则提取字符串 """
        r = re.compile(regex)
        assert r.groups > 0
        mcs = r.findall(text)
        if r.groups > 1:
            return mcs and [x for x in mcs[0]] or list(itertools.repeat('', r.groups))
        else:
            return mcs and mcs[0] or ''
