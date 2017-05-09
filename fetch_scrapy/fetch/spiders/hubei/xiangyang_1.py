import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class xiangyang_1Spider(scrapy.Spider):
    """
    @title: 襄阳市公共资源交易网
    @href: http://www.xysztb.gov.cn/xyzbw/
    """
    name = 'hubei/xiangyang/1'
    alias = '湖北/襄阳'
    allowed_domains = ['xysztb.gov.cn']
    start_urls = [
        ('http://www.xysztb.gov.cn/xyzbw/jyxx/002002/002002001/', '招标公告/政府采购'),
        ('http://www.xysztb.gov.cn/xyzbw/jyxx/002002/002002003/', '中标公告/政府采购'),
        ('http://www.xysztb.gov.cn/xyzbw/jyxx/002001/002001001/', '招标公告/建设工程'),
        ('http://www.xysztb.gov.cn/xyzbw/jyxx/002001/002001004/', '中标公告/建设工程'),
    ]
    # custom_settings = {'DOWNLOAD_DELAY': 1.0}

    link_extractor = MetaLinkExtractor(css='#moreinfosub tr > td > a[target=_blank]',
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
