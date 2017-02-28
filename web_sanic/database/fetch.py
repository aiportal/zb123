import peewee
from peewee_async import Manager, PooledMySQLDatabase
from datetime import datetime, date
from typing import List, Iterable


host = __debug__ and 'data.ultragis.com' or '127.0.0.1'
db_fetch = PooledMySQLDatabase(host=host, database='fetch', user='root', password='lq1990', charset='utf8')


class BaseModel(peewee.Model):
    class Meta:
        database = db_fetch


# 信息采集表
class GatherInfo(BaseModel):
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


# 异常信息表
class EventLog(BaseModel):
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


class AsyncManager(Manager):
    database = db_fetch

    async def get_content(self, uuid):
        """ 获取详情页信息 """
        query = ContentInfo.select().where(ContentInfo.uuid == uuid)
        result = await self.execute(query)
        return result[0] if len(result) > 0 else None

    async def query_filtered_gathers(self, day: date, page: int=1, size: int=20,
                                     sources=(), subjects=(), keys=()) -> List[GatherInfo]:
        """ 查询信息列表：只显示符合条件的记录 """
        assert size < 100

        # 按天查询
        query = GatherInfo.select().where(GatherInfo.day == day)

        # 筛选条件
        if sources:
            query = query.where(GatherInfo.source << sources)
        if subjects:
            exp = False
            for subject in subjects:
                exp = exp | GatherInfo.subject.startswith(subject)
            query = query.where(exp)
        if keys:
            exp = False
            for key in keys:
                exp = exp | GatherInfo.title.contains(key)
            query = query.where(exp)

        # 排序和分页
        query = query.order_by(+GatherInfo.source, +GatherInfo.subject, -GatherInfo.title)
        query = query.limit(size).offset((page - 1) * size)

        # 返回查询结果
        result = await self.execute(query)
        return [x for x in result]

    async def query_sorted_gathers(self, day: date, page: int=1, size: int=20,
                                   sources=(), subjects=(), keys=()) -> List[GatherInfo]:
        """ 查询信息列表：按条件排序，但返回全部记录 """
        assert size < 100

        # sql example:
        # select uuid, source, subject, title,
        # 	if(source in ("qinghai", "tianjin"), 2000, 1000) as v_source,
        # 	if(subject like '预公告%', 90, 0) + if(subject like '招标公告%', 89, 0) as v_subject,
        # 	if(title like '%工程%', 100, 0) + if(title like '%电子%', 99, 0) + if(title like '%软件%', 99, 0) as v_key
        # from gather_full where day='2017-02-20'
        # order by v_source desc, source, v_subject + v_key, title desc

        # 招标来源匹配度
        col_source_match = peewee.fn.IF(True, 0, 0)
        if sources:
            col_source_match += peewee.fn.IF(GatherInfo.source << sources, 2000, 1000)

        # 招标类型匹配度
        col_subject_match = peewee.fn.IF(True, 0, 0)
        for i, subject in enumerate(subjects):
            col_subject_match += peewee.fn.IF(GatherInfo.subject.startswith(subject), (90 - i), 0)

        # 关键词匹配度
        col_key_match = peewee.fn.IF(True, 0, 0)
        for i, key in enumerate(keys):
            col_key_match += peewee.fn.IF(GatherInfo.title.contains(key), (100 - i), 0)

        # 查询
        query = GatherInfo.select().where(GatherInfo.day == day).order_by(
            -col_source_match, GatherInfo.source, -col_subject_match, -col_key_match
        )
        query = query.limit(size).offset((page - 1) * size)

        result = await self.execute(query)
        return [x for x in result]

    async def query_day_totals(self, day: date) -> dict:
        query = GatherInfo.select(GatherInfo.source, peewee.fn.Count(GatherInfo.uuid).alias('count'))\
            .where(GatherInfo.day == str(day))\
            .group_by(GatherInfo.source)
        result = self.execute(query)
        return {x.source: x.count for x in result}
