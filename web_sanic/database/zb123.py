import peewee
from peewee_async import Manager, PooledMySQLDatabase
from datetime import datetime, date
import json


db_zb123 = PooledMySQLDatabase(host='127.0.0.1', database='zb123', user='root', passwd='lq1990', charset='utf8')
zb123 = Manager(db_zb123)


class JSONField(peewee.CharField):
    """ JSON字段 """
    def db_value(self, value: dict):
        return value and json.dumps(value, ensure_ascii=False) or None

    def python_value(self, value) -> dict:
        return json.loads(value or '{}') or None


class Zb123Model(peewee.Model):
    class Meta:
        database = db_zb123


# 用户信息
class UserInfo(Zb123Model):
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
        try:
            return UserInfo.get(uid=uid)
        except:
            return None
UserInfo.create_table(True)


class FilterRule(Zb123Model):
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
    suggest = property(lambda self: (self.filter or {}).get('suggest', []))     # 关键词选项

    @staticmethod
    def get_rule(uid: str):
        query = FilterRule.select().where(FilterRule.uid == uid).where(FilterRule.active == True)
        return query[0] if len(query) > 0 else None
FilterRule.create_table(True)


class AnnualFee(Zb123Model):
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
    def get_orders(uid: str):
        """ VIP用户订单列表 """
        query = AnnualFee.select().where(AnnualFee.uid == uid).order_by(-AnnualFee.start)
        return [x for x in query]

    @staticmethod
    def is_vip(uid: str) -> bool:
        """ 是否VIP用户"""
        query = AnnualFee.select().where(AnnualFee.uid == uid).order_by(-AnnualFee.start).limit(1)
        fee = query[0] if len(query) > 0 else None
        return fee and date.today() <= fee.end or False
AnnualFee.create_table(True)


class SuggestInfo(Zb123Model):
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


class RuntimeEvent(Zb123Model):
    """ 异常信息 """
    class Meta:
        db_table = 'event_log'
    id = peewee.PrimaryKeyField()
    level = peewee.CharField(max_length=50, help_text='错误类型')
    info = peewee.CharField(max_length=2000, help_text='错误信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    async def log_event(level: str, info: str):
        zb123.create(RuntimeEvent, level=level, info=info)
RuntimeEvent.create_table(True)


class AccessLog(Zb123Model):
    """ 页面访问日志 """
    class Meta:
        db_table = 'access_log'
    id = peewee.PrimaryKeyField()
    uid = peewee.CharField(max_length=50, help_text='用户ID')
    url = peewee.CharField(max_length=255, help_text='网址')
    info = peewee.CharField(max_length=2000, null=True, help_text='附加信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    async def log_access(uid: str, url: str, info: dict):
        await zb123.create(AccessLog, uid=uid, url=url, info=json.dumps(info, ensure_ascii=False))
AccessLog.create_table(True)


class SysConfig(Zb123Model):
    class Meta:
        db_table = 'sys_config'
        indexes = ((('subject', 'key'), True),)
    id = peewee.PrimaryKeyField()
    subject = peewee.CharField(max_length=50, help_text='分类')
    key = peewee.CharField(max_length=50, help_text='键')
    value = peewee.CharField(max_length=255, null=True, help_text='值')
    info = peewee.CharField(max_length=255, null=True, help_text='说明')

    @staticmethod
    def get_items(subject):
        query = SysConfig.select().where(SysConfig.subject == subject).order_by(+SysConfig.id)
        return [x for x in query]

    @staticmethod
    def get_item(subject, key):     # type:SysConfig
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
