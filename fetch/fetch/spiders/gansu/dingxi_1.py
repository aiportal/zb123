import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class dingxi_1Spider(scrapy.Spider):
    """
    @title: 定西市公共资源交易中心
    @href: http://www.dxggzy.com/dxztb/
    """
    name = 'gansu/dingxi/1'
    alias = '甘肃/定西'
    allowed_domains = ['dxggzy.com']
    start_urls = [
        ('http://www.dxggzy.com/dxztb/jyxx/004002/004002001/004002001001/', '招标公告/政府采购'),
        ('http://www.dxggzy.com/dxztb/jyxx/004002/004002003/004002003001/', '中标公告/政府采购'),

        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001001/004001001001/', '招标公告/建设工程/房建市政'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001002/004001002001/', '招标公告/建设工程/交通'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001003/004001003001/', '招标公告/建设工程/水利'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001004/004001004001/', '招标公告/建设工程/其他'),

        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001001/004001001008/', '中标公告/建设工程/房建市政'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001002/004001002008/', '中标公告/建设工程/交通'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001003/004001003008/', '中标公告/建设工程/水利'),
        ('http://www.dxggzy.com/dxztb/jyxx/004001/004001004/004001004008/', '中标公告/建设工程/其他'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 1.6}

    link_extractor = MetaLinkExtractor(css='div.content tr > td > a[target=_blank]',
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
