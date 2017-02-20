import peewee
from peewee_async import Manager, MySQLDatabase
import uuid


db_telephone = MySQLDatabase(host='127.0.0.1', database='telephone', user='root', password='lq1990', charset='utf8')
telephone = Manager(db_telephone)


class TelephoneModel(peewee.Model):
    class Meta:
        database = db_telephone


class CompanyInfo(TelephoneModel):
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
CompanyInfo.create_table(True)


class JobIndex(TelephoneModel):
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
        JobIndex.get_or_create(uuid=url_hash, state=state)
JobIndex.create_table(True)
