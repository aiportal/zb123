from sanic.views import HTTPMethodView
from sanic.request import Request
from .core import json_response
from database import FilterRule, AnnualFee, SysConfig, SuggestInfo
from datetime import datetime, date, timedelta
import hashlib
import json


class UserInfoApi(HTTPMethodView):
    """ 界面初始化信息 """
    def __init__(self):
        super().__init__()

        # 信息来源列表
        self.sources = [(x.key, x.value) for x in SysConfig.get_items('source')]

        # 信息类型列表
        self.subjects = [(x.key, x.value) for x in SysConfig.get_items('subject')]

    def get(self, request: Request):
        """ 获取界面初始化信息 """
        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 筛选规则
        rule = FilterRule.get_rule(uid) or FilterRule()

        # 信息来源
        sources = [{'value': k, 'text': v, 'select': k in rule.sources} for k, v in self.sources]

        # 信息类型
        subjects = [{'text': k, 'select': k in rule.subjects} for k, v in self.subjects]

        # 关键词
        keys = [{'text': x, 'select': x in rule.keys} for x in rule.suggest]

        # 会员信息
        orders = AnnualFee.get_orders(uid)    # 付费信息列表
        if not orders:
            user = {'vip': False, 'pays': None, 'end': None}
        else:
            user = {'vip': True, 'end': str(orders[0].end),
                    'pays': [{'day': str(x.day), 'fee': x.amount, 'start': str(x.start), 'end': str(x.end),
                              'order': x.order_no} for x in orders]}

        # 日期列表（最近30天）
        days = [str(date.today() + timedelta(x)) for x in reversed(range(-29, 1))]

        # 返回信息
        return json_response({
            'rule': {
                'sources': sources,
                'subjects': subjects,
                'keys': keys,
            },
            'user': user,
            'days': days,
        })


class UserRuleApi(HTTPMethodView):
    def __init__(self):
        super().__init__()

        # 信息来源列表
        self.sources = [(x.key, x.value) for x in SysConfig.get_items('source')]

        # 信息类型列表
        self.subjects = [(x.key, x.value) for x in SysConfig.get_items('subject')]

    def get(self, request: Request):
        """ 获取筛选规则 """
        uid = request.cookies.get('uid')
        assert uid

        # 查询筛选规则
        rule = FilterRule.get_rule(uid)

        # 信息来源
        sources = [{'value': k, 'text': v, 'select': k in rule.sources} for k, v in self.sources]

        # 信息类型
        subjects = [{'text': x, 'select': x in rule.subjects} for x in self.subjects]

        # 关键词
        keys = [{'text': x, 'select': x in rule.keys} for x in rule.suggest]

        return json_response({
            'sources': sources,
            'subjects': subjects,
            'keys': keys
        })

    def post(self, request: Request):
        """ 保存筛选规则 """
        uid = request.cookies.get('uid')
        assert uid

        # 每位用户可保存多条规则，目前仅一条规则可用

        # 用md5避免用户多次保存相同的规则
        rule = request.json
        rule_md5 = self.md5(rule)

        # 将用户的所有规则标记为不可用
        update = FilterRule.update(active=False).where(FilterRule.uid == uid)
        update.execute()

        # 插入或更新规则
        rec, _ = FilterRule.get_or_create(uid=uid, uuid=rule_md5, defaults={'filter': rule})
        rec.active = True,
        rec.time = datetime.now()
        rec.save()

        return json_response({'success': True})

    @staticmethod
    def md5(data: dict):
        """ 计算md5值 """
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest().upper()


class SuggestApi(HTTPMethodView):
    """ 意见反馈 """
    def post(self, request: Request):
        uid = request.cookies.get('uid')
        data = request.json
        rec = SuggestInfo(uid=uid, content=data['content'], tel=data.get('tel'))
        rec.save()
        self.notice_admin(data)
        return json_response({'success': True})

    @staticmethod
    def notice_admin(data):
        """ 通知管理员 """
        from weixin import wx_zb123
        msg = '来自 {0} 的消息：{1}'.format(data.get('tel'), data['content'])
        try:
            for openid in wx_zb123.admin:
                wx_zb123.custom_send_text(openid, msg)
        except Exception as ex:
            pass
