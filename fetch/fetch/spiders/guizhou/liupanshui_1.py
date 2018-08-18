import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin, urlsplit
import json
import re


class liupanshui_1Spider(scrapy.Spider):
    """
    @title: 六盘水公共资源交易网
    @href: http://www.lpsggzy.cn/index.html
    """
    name = 'guizhou/liupanshui/1'
    alias = '贵州/六盘水'
    allowed_domains = ['lpsggzy.cn']
    start_urls = ['http://www.lpsggzy.cn/www/ajax_list.php']
    base_param = {'titlelen': '60', 'pageno': '1', 'row_num': '12'}
    start_params = [
        ('招标公告/政府采购', {'module_class': '4B', 'inf_type': '4B1'}),
        ('中标公告/政府采购', {'module_class': '4B', 'inf_type': '4B2'}),
        ('废标公告/政府采购', {'module_class': '4B', 'inf_type': '4B3'}),
        ('招标公告/建设工程', {'module_class': '4A', 'inf_type': '4A1'}),
        ('中标公告/建设工程', {'module_class': '4A', 'inf_type': '4A2'}),
        ('废标公告/建设工程', {'module_class': '4A', 'inf_type': '4A3'}),
    ]
    detail_url = 'http://www.lpsggzy.cn/www/ajax_content.php'
    default_headers = {'X-REQUESTED-WITH': 'XMLHttpRequest'}

    def start_requests(self):
        url = self.start_urls[0]
        for subject, param in self.start_params:
            data = dict(subject=subject)
            param.update(**self.base_param)
            yield scrapy.FormRequest(url, formdata=param, headers=self.default_headers,
                                     meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ JSON """
        pkg = json.loads(response.text)
        for ln in re.split('</li>\s*<li>', pkg['con']):
            row = {
                'day': SpiderTool.re_text('<span>(.+)</span>', ln),
                'href': SpiderTool.re_text('href="([^"]+)"', ln),
                'title': SpiderTool.re_text('title="([^"]+)"', ln),
                'text': SpiderTool.re_text('>(.+)</a>', ln),
            }
            top_url = urljoin(response.url, row['href'])
            query = urlsplit(top_url).query
            row.update(**response.meta['data'])
            yield scrapy.Request(self.detail_url, method='POST', body=query, headers=self.default_headers,
                                 meta={'data': row, 'top_url': top_url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "ret_data": {
                "title": "六盘水市公安局业务技术用房强电系统建设项目 （二次招标）废标公告",
                "subhead": "<span>发布时间：</span>2017年05月05日<span>来源：</span>六盘水市公安局<span>浏览次数：</span>48",
                "con": "<html...>",
                "download": ""
            }
        }
        """
        pkg = json.loads(response.text)['ret_data']
        data = response.meta['data']
        body = [pkg['con']]

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body
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
