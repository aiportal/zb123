from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import logging
from database import EventLog
import os


# Set the current directory as the working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))


# Set the log level for peewee
logging.getLogger('peewee').setLevel(logging.ERROR)


# log startup event
EventLog.log_event('main', 'START', ' '.join(sys.argv), info={'pid': os.getpid()})


# start spiders
process = CrawlerProcess(get_project_settings())
spiders = process.spider_loader.list()
args = sys.argv[1:]
if args:
    spiders = [x for x in spiders if x in args or x.split('/')[0] in args]
if '-full' in args:
    process.settings['MAX_SKIP'] = sys.maxsize
for spider in spiders:
    process.crawl(process.spider_loader.load(spider))
process.start()


# log stopped event
EventLog.log_event('main', 'STOP', ' '.join(sys.argv), info={'pid': os.getpid()})

