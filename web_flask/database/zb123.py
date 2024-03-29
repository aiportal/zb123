import peewee
from playhouse.pool import PooledMySQLDatabase
from .core import JSONField
from datetime import datetime, date
import platform
from typing import List


host = platform.system() == 'Windows' and 'data.ultragis.com' or '127.0.0.1'
db_zb123 = PooledMySQLDatabase(host=host, database='zb123', user='root', password='Bayesian@2018', charset='utf8mb4',
                               max_connections=32)


class BaseModel(peewee.Model):
    class Meta:
        database = db_zb123


# 用户信息
class UserInfo(BaseModel):
    class Meta:
        db_table = 'user'
    uid = peewee.CharField(primary_key=True, max_length=50, help_text='union_id')
    nickname = peewee.CharField(max_length=50, null=True)
    info = JSONField(max_length=2000, help_text='用户信息')                     # type: dict
    subscribe = peewee.DateField(help_text='订阅号的首次关注时间')
    tags = peewee.CharField(max_length=255, null=True, help_text='标签列表')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    zb123 = peewee.CharField(max_length=50, index=True, null=True, help_text='订阅号openid')
    bayesian = peewee.CharField(max_length=50, index=True, null=True, help_text='服务号openid')
    company = peewee.CharField(max_length=50, index=True, null=True, help_text='企业号openid')

    @staticmethod
    def get_user(uid: str):
        query = UserInfo.select().where(UserInfo.uid == uid)
        return query[0] if len(query) > 0 else None

    @staticmethod
    def user_exists(uid: str) -> bool:
        return UserInfo.select().where(UserInfo.uid == uid).exists()
UserInfo.create_table(True)


class FilterRule(BaseModel):
    class Meta:
        db_table = 'rule'
    id = peewee.PrimaryKeyField()
    uid = peewee.CharField(max_length=50, index=True, help_text='union_id')
    uuid = peewee.CharField(max_length=50, index=True, help_text='md5(filter)')
    filter = JSONField(max_length=2000, help_text='筛选规则')
    active = peewee.BooleanField(default=True, help_text='是否可用')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    name = property(lambda self: (self.filter or {}).get('name', ''))
    sources = property(lambda self: (self.filter or {}).get('sources', []))     # 信息来源列表
    subjects = property(lambda self: (self.filter or {}).get('subjects', []))   # 信息分类列表
    keys = property(lambda self: (self.filter or {}).get('keys', []))           # 关键词列表
    suggests = property(lambda self: (self.filter or {}).get('suggests', []))     # 关键词选项

    @staticmethod
    def get_rule(uid: str):
        query = FilterRule.select().where(FilterRule.uid == uid).where(FilterRule.active == True)\
            .order_by(-FilterRule.time).limit(1)
        return query[0] if len(query) > 0 else None
FilterRule.create_table(True)


class AnnualFee(BaseModel):
    """ 年费信息 """
    class Meta:
        db_table = 'fee'
    id = peewee.PrimaryKeyField()
    uid = peewee.CharField(max_length=50, index=True)           # union_id
    nickname = peewee.CharField(max_length=50, null=True)
    day = peewee.DateField()                                    # 付费日期
    amount = peewee.IntegerField()                              # 付费金额（元）
    start = peewee.DateField()                                  # 会员权益起始时间
    end = peewee.DateField()                                    # 会员权益结束时间
    order_no = peewee.CharField(max_length=50)                  # zb123订单号
    order_id = peewee.CharField(max_length=50, index=True)      # 微信订单号
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    def is_vip(uid: str):
        query = AnnualFee.select().where(AnnualFee.uid == uid).order_by(-AnnualFee.start).limit(1)
        record = query[0] if len(query) > 0 else None
        return record and date.today() < record.end or False

    @staticmethod
    def get_orders(uid: str):
        query = AnnualFee.select().where(AnnualFee.uid == uid).order_by(-AnnualFee.start).limit(10)
        return [x for x in query]
AnnualFee.create_table(True)


class SuggestInfo(BaseModel):
    """ 意见反馈 """
    class Meta:
        db_table = 'suggest'
    id = peewee.PrimaryKeyField()
    uid = peewee.CharField(max_length=50, help_text='用户ID')
    nickname = peewee.CharField(max_length=50, null=True, help_text='用户昵称')
    tel = peewee.CharField(max_length=50, null=True, help_text='联系方式')
    content = peewee.CharField(max_length=255, help_text='内容')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')
SuggestInfo.create_table(True)


class RuntimeEvent(BaseModel):
    """ 异常信息 """
    class Meta:
        db_table = 'event_log'
    id = peewee.PrimaryKeyField()
    level = peewee.CharField(max_length=50, help_text='错误类型')
    info = peewee.CharField(max_length=2000, help_text='错误信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    def log_event(level: str, info: dict):
        RuntimeEvent.create(level=level, info=info)
RuntimeEvent.create_table(True)


class AccessLog(BaseModel):
    """ 页面访问日志 """
    class Meta:
        db_table = 'access_log'
    id = peewee.PrimaryKeyField()
    uid = peewee.CharField(max_length=50, help_text='用户ID')
    url = peewee.CharField(max_length=255, help_text='网址')
    info = JSONField(max_length=2000, null=True, help_text='附加信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    def log_access(uid: str, url: str, info: dict):
        AccessLog.create(uid=uid, url=url, info=info)
AccessLog.create_table(True)


class SysConfig(BaseModel):
    class Meta:
        db_table = 'sys_config'
        indexes = ((('subject', 'key'), True),)
    id = peewee.PrimaryKeyField()
    subject = peewee.CharField(max_length=50, help_text='分类')
    key = peewee.CharField(max_length=50, help_text='键')
    value = peewee.CharField(max_length=255, null=True, help_text='值')
    info = peewee.CharField(max_length=2000, null=True, help_text='说明')

    @staticmethod
    def get_items(subject: str) -> list:
        query = SysConfig.select().where(SysConfig.subject == subject).order_by(+SysConfig.id)
        return [x for x in query]

    @staticmethod
    def get_item(subject: str, key: str):     # type:SysConfig
        query = SysConfig.select().where(SysConfig.subject == subject).where(SysConfig.key == key)
        return query[0] if len(query) > 0 else SysConfig(**{'subject': subject, 'key': key})

    @staticmethod
    def set_item(subject, key, value, info=''):
        rec, is_new = SysConfig.get_or_create(subject=subject, key=key,
                                              defaults={'value': str(value), 'info': info})
        if not is_new:
            rec.value = str(value)
            rec.save()
SysConfig.create_table(True)

if SysConfig.select().count() < 3:
    from .zb123_data import sys_config_data
    for item in sys_config_data:
        SysConfig.create(id=item[0], subject=item[1], key=item[2], value=item[3], info=item[4])
