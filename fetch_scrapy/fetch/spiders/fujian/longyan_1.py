import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class longyan_1Spider(scrapy.Spider):
    """
    @title: 龙岩市公共资源交易中心
    @href: http://www.lyggzy.com.cn/lyztb/
    """
    name = 'fujian/longyan/1'
    alias = '福建/龙岩'
    allowed_domains = ['lyggzy.com.cn']
    start_urls = [
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081001/081001003/', '招标公告/建设工程'),
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081001/081001005/', '中标公告/建设工程'),
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008001/081008001001/', '招标公告/建设工程'),    # 新罗
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008002/081008002001/', '招标公告/建设工程'),    # 长汀
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008003/081008003001/', '招标公告/建设工程'),    # 永定
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008004/081008004001/', '招标公告/建设工程'),    # 上杭
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008005/081008005001/', '招标公告/建设工程'),    # 武平
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008006/081008006001/', '招标公告/建设工程'),    # 连城
        ('http://www.lyggzy.com.cn/lyztb/gcjs/081008/081008007/081008007001/', '招标公告/建设工程'),    # 漳平

        ('http://www.lyggzy.com.cn/lyztb/zfcg/082003/082003001/', '招标公告/政府采购'),
        ('http://www.lyggzy.com.cn/lyztb/zfcg/082003/082003002/', '中标公告/政府采购'),
        ('http://www.lyggzy.com.cn/lyztb/zfcg/082003/082003007/', '预公告/政府采购'),
        ('http://www.lyggzy.com.cn/lyztb/zfcg/082001/082001002/', '招标公告/其他'),
        ('http://www.lyggzy.com.cn/lyztb/zfcg/082001/082001003/', '中标公告/其他')
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.2}

    link_extractor = MetaLinkExtractor(css='ul.list > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta, 'dont_redirect': True}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#mainContent, div.fjsize')
        prefix = '^\[\w{2,8}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
