import peewee
from playhouse.sqlite_ext import *
import uuid
import platform


# db_telephone = SqliteExtDatabase('../telephone.db')
if platform.system() == 'Windows':
    db_telephone = peewee.MySQLDatabase(host='192.168.3.198', user='root', passwd='lq1990', port=3306, database='telephone', charset='utf8')
else:
    db_telephone = peewee.MySQLDatabase(host='127.0.0.1', user='root', passwd='lq1990', port=3306, database='telephone', charset='utf8')


class BaseModel(peewee.Model):
    class Meta:
        database = db_telephone


class CompanyInfo(BaseModel):
    class Meta:
        db_table = 'company'
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


class JobIndex(BaseModel):
    class Meta:
        db_table = 'urls'
    uuid = peewee.FixedCharField(primary_key=True, max_length=32, help_text='URL的HASH值')
    state = peewee.IntegerField(default=0, help_text='Url的状态或分类')

    @staticmethod
    def url_hash(url):
        return str(uuid.uuid3(uuid.NAMESPACE_URL, url)).replace('-', '')

    @staticmethod
    def url_exists(url):
        url_hash = JobIndex.url_hash(url)
        return JobIndex.select().where(JobIndex.uuid == url_hash).exists()

    @staticmethod
    def url_add(url, state=0):
        url_hash = JobIndex.url_hash(url)
        return JobIndex.insert(uuid=url_hash, state=state).execute()


if not CompanyInfo.table_exists():
    CompanyInfo.create_table()
if not JobIndex.table_exists():
    JobIndex.create_table()
