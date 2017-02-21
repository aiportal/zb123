from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import logging
from database import EventLog
import os
from datetime import datetime


# 设置工作目录
os.chdir(os.path.dirname(os.path.realpath(__file__)))


# 设置peewee的日志级别
logging.getLogger('peewee').setLevel(logging.ERROR)


# log startup
EventLog(source='process', url=str(os.getpid()), level='STARTUP', status=1001, info=str(datetime.now()), data='').save()


# 启动spiders
process = CrawlerProcess(get_project_settings())
spiders = process.spider_loader.list()
args = sys.argv[1:]
if args:
    spiders = [x for x in spiders if x in args or x.split('/')[0] in args]
if '-all' in args:
    process.settings['MAX_SKIP'] = sys.maxsize
for spider in spiders:
    process.crawl(process.spider_loader.load(spider))
process.start()


# log stopped
EventLog(source='process', url=str(os.getpid()), level='STOPPED', status=1002, info=str(datetime.now()), data='').save()
