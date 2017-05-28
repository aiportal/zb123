import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class shizuishan_1Spider(scrapy.Spider):
    """
    @title: 石嘴山市公共资源交易中心
    @href: http://www.szsggzy.cn/
    """
    name = 'ningxia/shizuishan/1'
    alias = '宁夏/石嘴山'
    allowed_domains = ['szsggzy.cn']
    start_urls = [
        # ('http://www.szsggzy.cn/morelink.aspx?type=12&index=0&isbg=0', '招标公告/政府采购'),
        # ('http://www.szsggzy.cn/morelink.aspx?type=17&index=0', '中标公告/政府采购'),
        # ('http://www.szsggzy.cn/morelink.aspx?type=12&index=0&isbg=1', '更正公告/政府采购'),
        # ('http://www.szsggzy.cn/morelink.aspx?type=12&index=1&isbg=0', '招标公告/建设工程'),
        # ('http://www.szsggzy.cn/morelink.aspx?type=17&index=1', '中标公告/建设工程'),
        # ('http://www.szsggzy.cn/morelink.aspx?type=12&index=1&isbg=1', '更正公告/建设工程'),
    ]
    custom_settings = {'COOKIES_ENABLED': True}

    link_extractor = NodesExtractor(css='#GV1 tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            target, argument = SpiderTool.re_text("__doPostBack\('(\w+)','(.+)'\)", row['href'])
            form = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': argument,
            }
            row.update(**response.meta['data'])
            headers = {'Cache-Control': 'max-age=0'}
            yield scrapy.FormRequest.from_response(response, formdata=form, meta={'data': row}, headers=headers,
                                                   callback=self.parse_item)
            break

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#Lb_nr') or response.css('#acticlesm')
        prefix = '^\[\w{2,8}\]'
        suffix = '\[\w{2,8}\]$'

        day = FieldExtractor.date(data.get('day') or response.css('#Lb_date'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        title = re.sub(suffix, '', title)
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
