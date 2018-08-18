import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class shanghai_1Spider(scrapy.Spider):
    """
    @title: 上海政府采购
    @href: http://www.zfcg.sh.gov.cn/
    """
    name = 'shanghai/1'
    alias = '上海'
    allowed_domains = ['zfcg.sh.gov.cn']
    start_urls = [
        ('http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore{0}'.format(k), v)
        for k, v in [
            ('&flag=cggg&bFlag=00&treenum=05', '招标公告/市级'),
            ('&flag=cjgg&bFlag=00&treenum=06', '中标公告/市级'),
            ('&flag=cggg&bFlag=qxgg&treenum=05', '招标公告/区县'),
            ('&flag=cjgg&bFlag=qxgg&treenum=06', '中标公告/区县'),
        ]
    ]

    link_extractor = NodesExtractor(css='#bulletininfotable_table tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        for row in rows:
            url = 'http://www.zfcg.sh.gov.cn/emeb_bulletin.do?method=showbulletin&bulletin_id={[value]}'.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#templateContext') or response.css('table.waibian')
        prefix1 = '^\w{1,5}公告：'
        prefix2 = '^\w{1,10}第[A-Z0-9-]+号信息-+'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix1, '', title)
        title = re.sub(prefix2, '', title)
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
