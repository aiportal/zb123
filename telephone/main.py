from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import logging
import os
import platform


# 服务器上配置 privoxy + lantern 代理
# if platform.system() != 'Windows':
#     os.environ.setdefault('https_proxy', 'http://127.0.0.1:8118')
# else:
#     os.environ.setdefault('https_proxy', 'http://data.ultragis.com:8118')


logging.getLogger('peewee').setLevel(logging.ERROR)
os.chdir(os.path.dirname(os.path.realpath(__file__)))

process = CrawlerProcess(get_project_settings())
# spiders = process.spider_loader.list()
spiders = ['mingluji']
for spider in spiders:
    process.crawl(process.spider_loader.load(spider))
process.start()

