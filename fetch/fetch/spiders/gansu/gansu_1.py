import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class gansu_1Spider(scrapy.Spider):
    """
    @title: 甘肃政府采购网
    @href: http://www.ccgp-gansu.gov.cn/
    """
    name = 'gansu/1'
    alias = '甘肃'
    allowed_domains = ['ccgp-gansu.gov.cn']
    start_urls = [
        ('http://www.ccgp-gansu.gov.cn/web/doSearch.action?'
         'op=%271%27&articleSearchInfoVo.classname={}'.format(k), v)
        for k, v in [
            ('1280101', '预公告/询价公告'),
            ('1280501', '招标公告'),
            ('12802', '中标公告'),
            ('12807', '废标公告'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='ul.Expand_SearchSLisi > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'days': '../p[1]//text()',
                                                    'tags': '../p[2]//text()'})

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
        body = response.css('div.conTxt')
        tags = [s.strip() for s in data.get('tags', '').split('|')] + ['']
        day_pub = SpiderTool.re_text('发布时间：([0-9-]+)', data.get('days', ''))

        day = FieldExtractor.date(day_pub, response.css('div.property'))
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
