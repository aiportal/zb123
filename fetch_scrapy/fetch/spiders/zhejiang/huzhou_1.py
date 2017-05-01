import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class huzhou_1Spider(scrapy.Spider):
    """
    @title: 湖州市公共资源交易中心
    @href: http://ggzy.huzhou.gov.cn/HZfront/
    """
    name = 'zhejiang/huzhou/1'
    alias = '浙江/湖州'
    allowed_domains = ['huzhou.gov.cn']
    start_urls = [
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021001/021001001/', '招标公告/建设工程'),
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021001/021001002/', '中标公告/建设工程'),
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021002/021002001/', '招标公告/交通'),
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021002/021002002/', '中标公告/交通'),
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021003/021003001/', '招标公告/水利'),
        ('http://ggzy.huzhou.gov.cn/HZfront/jcjs/021003/021003002/', '中标公告/水利'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024001/024001003/', '预公告/政府采购/集中'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024001/024001001/', '招标公告/政府采购/集中'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024001/024001002/', '中标公告/政府采购/集中'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024002/024002003/', '预公告/政府采购/分散'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024002/024002001/', '招标公告/政府采购/分散'),
        ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024002/024002002/', '中标公告/政府采购/分散'),
        ('http://ggzy.huzhou.gov.cn/HZfront/ylcg/025001/025001001/', '招标公告/医疗采购/集中'),
        ('http://ggzy.huzhou.gov.cn/HZfront/ylcg/025001/025001002/', '中标公告/医疗采购/集中'),
        ('http://ggzy.huzhou.gov.cn/HZfront/ylcg/025002/025002001/', '招标公告/医疗采购/分散'),
        ('http://ggzy.huzhou.gov.cn/HZfront/ylcg/025002/025002002/', '中标公告/医疗采购/分散'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a.WebList_sub',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent, .infodetail')

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
