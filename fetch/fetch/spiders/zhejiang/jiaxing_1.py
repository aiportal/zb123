import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class ZhejiangJiaxing1Spider(scrapy.Spider):
    """
    @title: 嘉兴市公共资源交易中心
    @href: http://www.jxzbtb.gov.cn/jxcms/jxztb/
    """
    name = 'zhejiang/jiaxing/1'
    alias = '浙江/嘉兴'
    allowed_domains = ['jxzbtb.gov.cn']
    start_urls = [
        ('http://www.jxzbtb.gov.cn/jxcms/jxztb/category/jygg/jsgcjy/list.html',
         [('//div[@class="com_box mb_5"][1]//ul/li//a', '招标公告/工程建设'),
          ('//div[@class="com_box mb_5"][3]//ul/li//a', '中标公告/工程建设')]),
        ('http://www.jxzbtb.gov.cn/jxcms/jxztb/category/jygg/zfcg/list.html',
         [('//div[@class="com_box mb_5"][1]//ul/li//a', '招标公告/政府采购'),
          ('//div[@class="com_box mb_5"][4]//ul/li//a', '中标公告/政府采购')]),
        ('http://www.jxzbtb.gov.cn/jxcms/jxztb/category/zfcgbjc/list.html',
         [('//div[@class="com_box mb_5"][1]//ul/li//a', '招标公告/政府采购'),
          ('//div[@class="com_box mb_5"][4]//ul/li//a', '中标公告/政府采购')]),
        ('http://www.jxzbtb.gov.cn/jxcms/jxztb/category/jygg/jdbmgz/list.html',
         [('//div[@class="com_box mb_5"][1]//ul/li//a', '招标公告/其他'),
          ('//div[@class="com_box mb_5"][2]//ul/li//a', '中标公告/其他')]),
    ]

    def start_requests(self):
        for url, subjects in self.start_urls:
            data = dict(subjects=subjects)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        subjects = response.meta['data']['subjects']
        for xpath, subject in subjects:
            extractor = MetaLinkExtractor(xpath=xpath, attrs_xpath={
                'text': './/text()', 'day': '../../span[last()]//text()'})
            links = extractor.links(response)
            for lnk in links:
                lnk.meta.update(subject=subject)
                yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.article_content') or response('#content, .append')

        day = FieldExtractor.date(data.get('day'), response.css('span.uptime'))
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
