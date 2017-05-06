import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class longnan_1Spider(scrapy.Spider):
    """
    @title: 陇南公共资源交易中心
    @href: http://www.lnsggzyjy.cn/
    """
    name = 'gansu/longnan/1'
    alias = '甘肃/陇南'
    allowed_domains = ['lnsggzyjy.cn']
    start_urls = [
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004002/004002001/', '招标公告/政府采购'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004002/004002003/', '中标公告/政府采购'),

        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004001/004001001/', '招标公告/建设工程/房建市政'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004005/004005001/', '招标公告/建设工程/水利'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004006/004006001/', '招标公告/建设工程/交通'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004007/004007001/', '招标公告/建设工程/医药'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004008/004008001/', '招标公告/建设工程/其他'),

        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004001/004001003/', '中标公告/建设工程/房建市政'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004005/004005003/', '中标公告/建设工程/水利'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004006/004006003/', '中标公告/建设工程/交通'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004004/004004003/', '中标公告/建设工程/医药'),
        ('http://www.lnsggzyjy.cn/lnzbw/jyxx/004008/004008003/', '中标公告/建设工程/其他'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="22"] > td > a[target=_blank]',
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
