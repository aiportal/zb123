import scrapy
from . import JsonMetaSpider, GatherItem
from . import DateExtractor, JsonLinkGenerator, JsonPageGenerator, HtmlContentExtractor
import json
from datetime import datetime


# 重庆市政府采购网：https://www.cqgp.gov.cn/
# 采购公告：https://www.cqgp.gov.cn/notices/list
# 索引页（JSON）：https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable?pi=3&ps=20&timestamp=1484788922991


class ChongqingSpider(JsonMetaSpider):
    name = 'chongqing'
    alias = '重庆'
    allowed_domains = ['cqgp.gov.cn']
    start_referer = 'https://www.cqgp.gov.cn/notices/list'
    start_urls = ['https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable?']
    start_params = {
        # 信息类型
        'type': {'301,303': '预公告', '300,302,304,3041,305,306,307,308': '中标公告',
                 '100,200,201,202,203,204,205,206,207,309,400,401,402,3091,4001': '招标公告/采购公告'},
        'pi': 1,        # 页码
        'ps': 20,       # 行数
        'timestamp': int(datetime.now().timestamp()*1000)
    }
    dict_purchase = {'100': '公开招标', '200': '邀请招标', '300': '竞争性谈判', '400': '询价', '500': '单一来源',
                     '800': '竞争性磋商', '6001': '电子竞价', '6002': '电子反拍'}

    link_generator = JsonLinkGenerator('/gwebsite/api/v1/notices/stable/{0[id]}', '/notices/{0[id]}',
                                       lambda x: x['notices'])
    page_generator = JsonPageGenerator('pi', 'ps', lambda x: x['total'])

    def parse_item(self, response):
        """ 解析详情页
        """
        data = response.meta['data']
        # "id": "362193974439669760",
        # "noticeType": 400,
        # "creatorOrgName": "王迪",
        # "issueTime": "2016-10-12 10:13:26",
        # "districtName": "市级",
        # "title": "2016年防汛抗旱物资采购（16A3366）分包3重新启动采购公告",
        # "projectDirectoryName": "货物类",
        # "projectPurchaseWay": 100,
        # "buyerName": "重庆市防汛抗旱抢险中心",
        # "agentName": "重庆市政府采购中心",
        # "bidEndTime": "2016-09-14 08:30:00",
        # "openBidTime": "2016-09-14 09:30:00"

        res = json.loads(response.text)
        item = res['notice']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('issueTime'))
        g['end'] = DateExtractor.extract(data.get('bidEndTime'), max_day=None)
        g['title'] = data.get('title')
        g['area'] = self.join_words(self.alias, data.get('districtName'))
        purchase_code = str(data.get('projectPurchaseWay'))
        g['subject'] = self.join_words(data['type'], self.dict_purchase.get(purchase_code, purchase_code))
        g['industry'] = data.get('projectDirectoryName')

        content_extractor = HtmlContentExtractor(xpath='./*')
        g['contents'] = content_extractor.extract_contents(scrapy.Selector(text=item.get('html')))
        g['pid'] = data.get('id')
        g['tender'] = data.get('buyerName')
        g['budget'] = item.get('projectBudget')
        g['tels'] = None
        if 'html' in item:
            del item['html']
        g['extends'] = res
        g['digest'] = data
        yield g
