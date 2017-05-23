import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class alashanmeng_1Spider(scrapy.Spider):
    """
    @title: 阿拉善盟
    @href: http://www.alsggzyjy.cn/website/zyjyzx/html/index.html
    """
    name = 'neimenggu/alashan/1'
    alias = '内蒙古/阿拉善盟'
    allowed_domains = ['alsggzyjy.cn']
    start_urls = [
        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=cg_zbgg', '招标公告/政府采购'),
        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=cg_zbgs', '中标公告/政府采购'),
        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=cg_bggg', '更正公告/政府采购'),
        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=fbgs', '中标公告/政府采购/废标公告'),

        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=zbgg', '招标公告/建设工程'),
        ('http://www.alsggzyjy.cn/website/zyjyzx/html/artList.html?catCode=zbgs', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='#div_list > ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../li[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#divZoom') or response.css('div.artContent')
        prefix = '^\[\w{2,5}\]\s*'

        day = FieldExtractor.date(data.get('day') or response.css('td.artBottom'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
