import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date, timedelta


class huaihua_1Spider(scrapy.Spider):
    """
    @title: 怀化市公共资源交易网
    @href: http://ggzy.huaihua.gov.cn/hhweb/
    """
    name = 'hunan/huaihua/1'
    alias = '湖南/怀化'
    allowed_domains = ['huaihua.gov.cn']
    start_urls = [
        ('http://ggzy.huaihua.gov.cn/hhweb/jygg/004002/004002001/', '招标公告/政府采购/货物'),
        ('http://ggzy.huaihua.gov.cn/hhweb/jygg/004002/004002002/', '招标公告/政府采购/工程'),
        ('http://ggzy.huaihua.gov.cn/hhweb/jygg/004002/004002003/', '招标公告/政府采购/服务'),
        ('http://ggzy.huaihua.gov.cn/hhweb/zbgs/022002/', '中标公告/政府采购'),
        ('http://ggzy.huaihua.gov.cn/hhweb/zbgg/027001/', '招标公告/建设工程'),
        ('http://ggzy.huaihua.gov.cn/hhweb/zbgs/022001/', '中标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.82}

    link_extractor = MetaLinkExtractor(
        css='tr[height="22"] > td > a[target=_blank], tr[height="18"] > td > a[target=_blank]',
        attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#TDContent, #trAttach')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        if 'error.aspx' in response.url and day < date.today():
            return []
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
