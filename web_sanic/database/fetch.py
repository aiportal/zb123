import peewee
from peewee_async import Manager, PooledMySQLDatabase
from datetime import datetime


db_fetch = PooledMySQLDatabase(host='127.0.0.1', database='fetch', user='root', passwd='lq1990', charset='utf8')
fetch = Manager(db_fetch)


class FetchModel(peewee.Model):
    class Meta:
        database = db_fetch


# 信息采集表
class GatherInfo(FetchModel):
    class Meta:
        db_table = 'gather_full'
    uuid = peewee.CharField(primary_key=True, max_length=50)
    day = peewee.DateField(index=True, help_text='招标日期')
    source = peewee.CharField(index=True, max_length=50, help_text='招标来源')
    url = peewee.CharField(index=True, help_text='详情页请求网址')
    end = peewee.DateField(null=True, help_text='截止日期')
    title = peewee.CharField(null=True, index=True, help_text='标题')
    area = peewee.CharField(null=True, max_length=50, help_text='地区(省、市等)')
    subject = peewee.CharField(null=True, index=True, help_text='信息分类(招标、中标等)')
    industry = peewee.CharField(null=True, help_text='行业分类(机械、软件等)')
    pid = peewee.CharField(null=True, max_length=255)
    tender = peewee.CharField(null=True, max_length=255)
    budget = peewee.CharField(null=True, help_text='预算金额/中标金额')
    tels = peewee.CharField(null=True, help_text='联系电话')
    extends = peewee.TextField(null=True, help_text='扩展信息(json格式)')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')
# GatherInfo.create_table(True)


class ContentInfo(FetchModel):
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
# ContentInfo.create_table(True)


# 异常信息表
class EventLog(FetchModel):
    class Meta:
        db_table = 'event_log'
    ID = peewee.PrimaryKeyField()
    source = peewee.CharField(max_length=50, help_text='来源')
    url = peewee.CharField(max_length=255, null=True, help_text='网址')
    level = peewee.CharField(max_length=50, null=True, help_text='类型')
    status = peewee.IntegerField(null=True, help_text='状态码')
    info = peewee.TextField(null=True, help_text='信息描述')
    data = peewee.TextField(null=True, help_text='附加信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')
# EventLog.create_table(True)
