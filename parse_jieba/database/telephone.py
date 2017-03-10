import peewee
from datetime import datetime, date

host = __debug__ and '192.168.3.198' or '127.0.0.1'
db_tel = peewee.MySQLDatabase(host=host, database='telephone', user='root', password='lq1990', charset='utf8')


class CompanyInfo(peewee.Model):
    class Meta:
        database = db_tel
        db_table = 'mingluji_company'
    id = peewee.PrimaryKeyField(help_text='ID')
    source = peewee.CharField(max_length=50, null=False, help_text='来源')
    area = peewee.CharField(max_length=50, null=False, help_text='行政区')
    city = peewee.CharField(max_length=50, null=True, help_text='地区')
    industry = peewee.CharField(max_length=50, null=True, help_text='行业分类')
    name = peewee.CharField(max_length=255, null=True, help_text='企业名称')
    tel = peewee.CharField(max_length=50, null=True, index=True, help_text='电话')
    url = peewee.CharField(max_length=255, null=True, help_text='网址')
    uuid = peewee.UUIDField(index=True, null=False, help_text='URL的HASH值')
    info = peewee.TextField(null=True, help_text='其他信息')


class StatInfo(peewee.Model):
    class Meta:
        database = db_tel
        db_table = 'mingluji_stat'
    id = peewee.PrimaryKeyField()
    area = peewee.CharField(max_length=50)
    word = peewee.CharField(max_length=50)
    count = peewee.IntegerField()
    time = peewee.DateTimeField(default=datetime.now)

StatInfo.create_table(True)

