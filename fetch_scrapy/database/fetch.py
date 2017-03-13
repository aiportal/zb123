import peewee
from .core import JSONField
from datetime import datetime, date
import uuid


host =  __debug__ and '127.0.0.1' or 'data.ultragis.com'
pwd = __debug__ and 'lq1990' or 'Bayesian@2018'
host = '127.0.0.1'
pwd = 'lq1990'
db_fetch = peewee.MySQLDatabase(host=host, database='fetch', user='root', password=pwd, charset='utf8')


class BaseModel(peewee.Model):
    class Meta:
        database = db_fetch

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls = type(self)

        # 确认数据库连接
        if db_fetch.is_closed():
            db_fetch.connect()
        # 确认数据表
        if not cls.table_exists():
            cls.create_table(fail_silently=True)


# 信息采集表
class GatherInfo(BaseModel):
    class Meta:
        db_table = 'gather_full'
        indexes = (
            (('day', 'source'), False), (('title', 'subject'), False),
        )
    uuid = peewee.CharField(primary_key=True, max_length=50, help_text='url的hash值')
    day = peewee.DateField(help_text='招标日期')
    source = peewee.CharField(max_length=50, help_text='招标来源')
    url = peewee.CharField(help_text='详情页请求网址')
    end = peewee.DateField(null=True, help_text='截止日期')
    title = peewee.CharField(null=True, help_text='标题')
    area = peewee.CharField(null=True, max_length=50, help_text='地区(省、市等)')
    subject = peewee.CharField(null=True, help_text='信息分类(招标、中标等)')
    industry = peewee.CharField(null=True, help_text='行业分类(机械、软件等)')
    pid = peewee.CharField(null=True, max_length=255)
    tender = peewee.CharField(null=True, max_length=255)
    budget = peewee.CharField(null=True, help_text='预算金额/中标金额')
    tels = peewee.CharField(null=True, help_text='联系电话')
    extends = peewee.TextField(null=True, help_text='扩展信息(json格式)')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')
GatherInfo.create_table(True)


class ContentInfo(BaseModel):
    class Meta:
        db_table = 'content_full'
    uuid = peewee.CharField(primary_key=True, max_length=50)
    day = peewee.DateField(index=True, help_text='招标日期')
    source = peewee.CharField(index=True, max_length=50, help_text='招标来源')
    index_url = peewee.CharField(null=True, help_text='索引页网址')
    top_url = peewee.CharField(null=True, help_text='框架详情页的顶层网址')
    real_url = peewee.CharField(null=True, help_text='详情页转向之后的真实网址(redirect)')
    html = peewee.BlobField(null=True, help_text='HTML内容(压缩)')
    digest = peewee.TextField(null=True, help_text='关键字段摘要')
    contents = peewee.TextField(null=True, help_text='招标详情(正文)')
    attachments = peewee.TextField(null=True, help_text='附件信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')
ContentInfo.create_table(True)


# 网址索引表
class JobIndex(BaseModel):
    class Meta:
        db_table = 'url_index'
    uuid = peewee.CharField(primary_key=True, max_length=50, help_text='url的hash值(gather表)')
    state = peewee.IntegerField(null=False, default=0, help_text='状态')

    @staticmethod
    def url_hash(url):
        return str(uuid.uuid3(uuid.NAMESPACE_URL, url)).replace('-', '')

    @staticmethod
    def url_exists(url):
        url_hash = JobIndex.url_hash(url)
        return JobIndex.select().where(JobIndex.uuid == url_hash).exists()

    @staticmethod
    def url_insert(url, state=0):
        url_hash = JobIndex.url_hash(url)
        JobIndex.get_or_create(uuid=url_hash, state=state)
JobIndex.create_table(True)


# 日志信息表
class EventLog(BaseModel):
    class Meta:
        db_table = 'event_log'
    ID = peewee.PrimaryKeyField()
    source = peewee.CharField(max_length=50)            # 招标来源（爬虫名称）
    level = peewee.CharField(max_length=50)             # 异常类型
    info = JSONField(max_length=2000)                   # 异常信息描述
    time = peewee.DateTimeField(default=datetime.now)   # 时间戳

    url = peewee.CharField()                            # 请求网址/
    status = peewee.IntegerField()                      # 状态码
    data = peewee.TextField()                           # 附加数据

    @staticmethod
    def log_event(source: str, level: str, msg: str='', info: dict={}):
        EventLog.create(source=source, level=level, url=msg, info=info, status=0, data=info)

EventLog.create_table(True)


# 异常记录表
class ExceptionLog(BaseModel):
    class Meta:
        db_table = 'exception_log'
    ID = peewee.PrimaryKeyField()
    source = peewee.CharField(max_length=50)                # 招标来源（爬虫名称）
    level = peewee.CharField(max_length=50)                 # 异常类型
    url = peewee.CharField(max_length=512, null=True)       # 请求网址
    info = JSONField(max_length=2000)                       # 异常信息描述
    time = peewee.DateTimeField(default=datetime.now)       # 时间戳

    @staticmethod
    def log_exception(source: str, level: str, url: str, info: dict):
        return ExceptionLog.create(source=source, level=level, url=url, info=info)

ExceptionLog.create_table(True)


# 系统设置表
class SysConfig(BaseModel):
    class Meta:
        db_table = 'sys_config'
        indexes = (
            (('subject', 'key'), True),
        )
    id = peewee.PrimaryKeyField()
    subject = peewee.CharField(max_length=50, help_text='分类')
    key = peewee.CharField(max_length=50, help_text='键')
    value = peewee.CharField(max_length=255, null=True, help_text='值')
    info = peewee.CharField(max_length=2000, null=True, help_text='附加信息')

    @staticmethod
    def get_items(subject):
        query = SysConfig.select().where(SysConfig.subject == subject)
        return {x.key: x.value for x in query} if len(query) > 0 else {}

    @staticmethod
    def get_item(subject, key):     # type:SysConfig
        query = SysConfig.select().where(SysConfig.subject == subject).where(SysConfig.key == key)
        return query[0] if len(query) > 0 else SysConfig(**{'subject': subject, 'key': key})

    @staticmethod
    def set_item(subject: str, key: str, value: str, info=None):
        rec, is_new = SysConfig.get_or_create(subject=subject, key=key, defaults={
            'value': str(value),
            'info': info
        })
        if not is_new:
            rec.value = str(value)
            rec.save()

SysConfig.create_table(True)
