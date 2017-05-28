import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class hebei_1Spider(scrapy.Spider):
    """
    @title: 河北省政府采购网
    @href: http://www.ccgp-hebei.gov.cn/
    """
    name = 'hebei/1'
    alias = '河北'
    allowed_domains = ['ccgp-hebei.gov.cn']
    start_urls = [
        ('http://www.ccgp-hebei.gov.cn/zfcg/web/getBidingList_1.html', '招标公告/政府采购',
         'http://www.ccgp-hebei.gov.cn/zfcg/{1}/bidingAnncDetail_{0}.html'),
        ('http://www.ccgp-hebei.gov.cn/zfcg/web/getBidWinAnncList_1.html', '中标公告/政府采购',
         'http://www.ccgp-hebei.gov.cn/zfcg/bidWinAnncDetail_{}.html'),
        ('http://www.ccgp-hebei.gov.cn/zfcg/web/getCorrectionAnncList_1.html', '更正公告/政府采购',
         'http://www.ccgp-hebei.gov.cn/zfcg/correctionAnncDetail_{}.html'),
        # ('http://www.ccgp-hebei.gov.cn/zfcg/web/getCancelBidAnncList_1.html', '废标公告/政府采购'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.08}

    link_extractor = NodesExtractor(css='tr[onclick^=watchContent]',
                                    attrs_xpath={'text': './/a//text()',
                                                 'day': './following-sibling::tr[1]/td/span[1]//text()'})

    def start_requests(self):
        for url, subject, detail in self.start_urls:
            data = dict(subject=subject, detail=detail)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        detail_url = response.meta['data']['detail']
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            fid, _, flag = SpiderTool.re_text("watchContent\('(\d+)'(,'(\d+)')?\)", row['onclick'])
            url = detail_url.format(fid, flag)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table[bgcolor="#bfdff1"], span.txt7:not([id]), a.blue')

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
