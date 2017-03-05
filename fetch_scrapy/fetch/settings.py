# -*- coding: utf-8 -*-
# Scrapy settings for fetch project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html


BOT_NAME = 'fetch'

SPIDER_MODULES = ['fetch.spiders']
NEWSPIDER_MODULE = 'fetch.spiders'
# COMMANDS_MODULE = 'fetch.commands'

# 压缩文件和CSV文件的保存路径
PACKAGE_FOLDER = '/prj/zb123/data/v2'

# 附件存储路径
FILES_STORE = '/prj/zb123/data/v2'

# 服务器返回空值时的重试次数
RETRY_TIMES = 3

# 索引页跳过重复网址的最大次数
MAX_SKIP = 5

# 日志
LOG_ENABLED = True
LOG_ENCODING = 'UTF-8'
LOG_LEVEL = __debug__ and 'DEBUG' or 'ERROR'    # DEBUG,INFO,WARNING,ERROR


DEFAULT_REQUEST_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip,deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
}

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

ITEM_PIPELINES = {
    # 'scrapy.pipelines.files.FilesPipeline': 1,
    # 'fetch.pipelines.AttachmentsPipeline': 10,
    'fetch.pipelines.MysqlPipeline': 200,
    'fetch.pipelines.ZipPackagePipeline': None,
    'fetch.pipelines.CsvPipeline': None,
}

DOWNLOADER_MIDDLEWARES = {
    'fetch.middlewares.EmptyRetryMiddleware': 200,
    'fetch.middlewares.HttpExceptionMiddleware': 300,
}

SPIDER_MIDDLEWARES = {
    'fetch.middlewares.SpiderExceptionMiddleware': 300,
}

EXTENSIONS = {
    'fetch.extensions.ExceptionLogExtension': 300,
    'fetch.extensions.SpiderStatsExtension': 500,
    'scrapy.extensions.memusage.MemoryUsage': 800,
}

# 限制内存占用
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 300

# 队列信息保存在磁盘上
# JOBDIR = './job'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = __debug__ and 0.1 or 1.0

# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False


# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


if True:
    import platform
    if platform.system() == 'Windows':
        PACKAGE_FOLDER = r'C:\Download\zb123'
        FILES_STORE = r'C:\Download\zb123'