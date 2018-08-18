import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class beijing_3Spider(scrapy.Spider):
    """
    @title: 北京市工程建设交易信息网
    @href: http://www.bcactc.com/default.aspx
    """
    name = 'beijing/3'
    alias = '北京'
    allowed_domains = ['bcactc.com']
    start_urls = [
        ('http://www.bcactc.com/home/gcxx/now_kcsjzbgg.aspx', '招标公告/建设工程', '勘察设计'),
        ('http://www.bcactc.com/home/gcxx/now_sgzbgg.aspx', '招标公告/建设工程', '施工'),
        ('http://www.bcactc.com/home/gcxx/now_jlzbgg.aspx', '招标公告/建设工程', '监理'),
        ('http://www.bcactc.com/home/gcxx/now_zyzbgg.aspx', '招标公告/建设工程', '专业'),
        ('http://www.bcactc.com/home/gcxx/now_clsbzbgg.aspx', '招标公告/建设工程', '材料设备'),
        ('http://www.bcactc.com/home/gcxx/now_tdzbgg.aspx', '招标公告/建设工程', '铁路'),
        ('http://www.bcactc.com/home/gcxx/now_ylzbgg.aspx', '招标公告/建设工程', '园林'),
        ('http://www.bcactc.com/home/gcxx/now_mhzbgg.aspx', '招标公告/建设工程', '民航'),
        ('http://www.bcactc.com/home/gcxx/now_jdzbgg.aspx', '招标公告/建设工程', '军队'),

        ('http://www.bcactc.com/home/gcxx/now_kcsjzbgs.aspx', '中标公告/建设工程', '勘察设计'),
        ('http://www.bcactc.com/home/gcxx/now_sgzbgs.aspx', '中标公告/建设工程', '施工'),
        ('http://www.bcactc.com/home/gcxx/now_jlzbgs.aspx', '中标公告/建设工程', '监理'),
        ('http://www.bcactc.com/home/gcxx/now_zyzbgs.aspx', '中标公告/建设工程', '专业'),
        ('http://www.bcactc.com/home/gcxx/now_clsbzbgs.aspx', '中标公告/建设工程', '材料设备'),
        ('http://www.bcactc.com/home/gcxx/now_tdzbgs.aspx', '中标公告/建设工程', '铁路'),
        ('http://www.bcactc.com/home/gcxx/now_ylzbgs.aspx', '中标公告/建设工程', '园林'),
        ('http://www.bcactc.com/home/gcxx/now_mhzbgs.aspx', '中标公告/建设工程', '军队'),
        ('http://www.bcactc.com/home/gcxx/now_jdzbgs.aspx', '中标公告/建设工程', '军队'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'end': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject, industry in self.start_urls:
            data = dict(subject=subject, industry=industry)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        # assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('td.context')

        day = FieldExtractor.date(data.get('end'))
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
        g.set(industry=[data.get('industry')])
        return [g]
