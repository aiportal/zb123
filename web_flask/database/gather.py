import peewee
from .fetch import BaseModel
from datetime import datetime
from .core import JSONField


class BidGather(BaseModel):
    class Meta:
        db_table = 'gather_new'
        indexes = ((('day', 'title', 'subject'), False),)

    uuid = peewee.CharField(primary_key=True, max_length=40)
    day = peewee.DateField(null=False, help_text='招标日期')
    title = peewee.CharField(null=True, help_text='标题')
    subject = peewee.CharField(null=True, help_text='信息分类(招标、中标等)')

    source = peewee.CharField(index=True, max_length=50, help_text='招标来源')
    area = peewee.CharField(null=True, help_text='地区(省、市等)')
    industry = peewee.CharField(null=True, help_text='行业分类(机械、软件等)')

    pid = peewee.CharField(null=True, help_text='项目ID')
    end = peewee.DateField(null=True, help_text='截止日期')
    inviter = peewee.CharField(null=True, help_text='招标单位')
    tender = peewee.CharField(null=True, help_text='中标单位')
    budget = peewee.CharField(null=True, help_text='预算金额/中标金额')
    tels = peewee.CharField(null=True, help_text='联系电话')

    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')


class BidContent(BaseModel):
    class Meta:
        db_table = 'content_new'
        indexes = ((('day', 'title'), False),)

    uuid = peewee.CharField(primary_key=True, max_length=50)
    day = peewee.DateField(null=True, help_text='招标日期')
    title = peewee.CharField(null=True, help_text='标题')

    index_url = peewee.CharField(null=True, help_text='索引页网址')
    top_url = peewee.CharField(null=True, help_text='框架页的顶层网址或 redirect 前的原始网址')
    real_url = peewee.CharField(null=True, help_text='详情页转向之后的真实网址(redirect)')

    contents = peewee.TextField(null=True, help_text='招标详情(正文)')
    digest = peewee.TextField(null=True, help_text='摘要信息')
    extends = JSONField(null=True, help_text='扩展信息')
    attachments = peewee.TextField(null=True, help_text='附件信息')

    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')


# if __name__ == '__main__':
#     from peewee import create_model_tables
#     create_model_tables([BidGather, BidContent])
