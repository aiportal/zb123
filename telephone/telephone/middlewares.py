import scrapy
import random
from datetime import datetime


class DynamicDelayMiddleware(object):
    def __init__(self):
        self.hours_delay = dict([(x, 0.1) for x in range(0, 24)])
        self.hours_delay.update([(0, 1.0)])
        self.hours_delay.update([(x, 0.6) for x in range(9, 10)])
        self.hours_delay.update([(x, 0.6) for x in range(14, 16)])

    def process_request(self, request, spider):
        hour = datetime.now().hour
        delay = self.hours_delay.get(hour)
        if delay:
            spider.download_delay = delay


class HttpProxyMiddleware(object):
    proxies = ['https://' + x for x in [
        '1.82.216.135:80',
        # '43.247.33.214:8080',
        # '163.47.11.218:8080',
        # '163.53.186.50:8080',
        # '218.103.60.205:8080',
    ]]

    def process_request(self, request, spider):
        request.meta['proxy'] = random.choice(self.proxies)


class UserAgentMiddleware(object):
    agents = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
        'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 7.0; InfoPath.3; .NET CLR 3.1.40767; Trident/6.0; en-IN)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/4.0; InfoPath.2; SV1; .NET CLR 2.0.50727; WOW64)',
        'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; MyIE2; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; MyIE2; InfoPath.2)',
    ]

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(self.agents)
