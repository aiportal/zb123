import requests
import json
import random
from database import ExceptionLog


"""
    每次启动时访问 proxy_url 获取代理网址列表
    每次请求时，如果meta参数中有proxy，就随机选取一个代理网址
"""

"""
http://www.zb123.bid:8088/
types	int	0: 高匿,1:匿名,2 透明
protocol	int	0: http, 1 https, 2 http/https
count	int	数量
country	str	取值为 国内, 国外
area	str	地区
"""


class DynamicProxyMiddleware(object):
    """ 动态IP代理 """
    proxy_url = 'http://www.zb123.bid:8088/?types=0&country=国内&protocol=0'
    proxy_list = []

    def __init__(self):
        if self.proxy_list:
            return
        resp = requests.get(self.proxy_url)
        proxy_list = json.loads(resp.text)
        self.proxy_list = [x for x in proxy_list if x[2] > 5]

    def process_request(self, request, spider):
        """ 设置代理 """
        if request.meta.get('proxy'):
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = 'http://{0[0]}:{0[1]}'.format(proxy)
        return None

    def process_exception(self, request, exception, spider):
        """ 更换代理或删除代理 """
        count = request.meta.get('proxy_retry', 0)      # 代理链接的重试次数
        if count > 2:
            ExceptionLog.log_exception(spider.name, 'PROXY', request.url, info={'ex': str(exception)})
            return None
        request.meta['proxy_retry'] = count + 1
        proxy = random.choice(self.proxy_list)
        request.meta['proxy'] = 'http://{0[0]}:{0[1]}'.format(proxy)
        return request
