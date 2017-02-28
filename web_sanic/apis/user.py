from sanic.views import HTTPMethodView
from sanic.request import Request
from .core import json_response
from database import zb123, SysConfig, FilterRule
from datetime import datetime, date, timedelta


class UserInfoApi(HTTPMethodView):
    """ 界面初始化信息 """
    def __init__(self):
        super().__init__()

        # 信息来源列表
        self.sources = SysConfig.get_items('source')
        # 信息类型列表
        self.subjects = SysConfig.get_items('subject')
        # 关键词建议列表
        self.suggests = SysConfig.get_items('suggest')

    async def get(self, request: Request):
        """ 获取界面初始化信息 """

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 筛选规则
        rule = (await zb123.get_rule(uid)) or FilterRule()

        # 信息来源
        sources = [{'value': x.key, 'text': x.value, 'select': x.key in rule.sources} for x in self.sources]

        # 信息类型
        subjects = [{'text': x.key, 'select': x.key in rule.subjects} for x in self.subjects]

        # 关键词
        keys = [{'text': x, 'select': x in rule.keys} for x in rule.suggests]

        # 会员信息
        orders = await zb123.get_orders(uid)    # 付费信息列表
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

    async def get_user_rule(self, uid: str) -> FilterRule:
        """ 获取用户的筛选规则 """
        rule = await zb123.get_rule(uid)

        # 如果没有设置，自动生成默认规则
        if not rule:
            user = await zb123.get_user(uid)
            province = user.info.get('province', '').lower()
            rule = {
                'sources': [x for x in self.sources if x.key == province],
                'subjects': [x for x in self.subjects if x.value != '0'],
                'keys': [],
                'suggests': [x for x in self.suggests if '*' in x.value or province in x.value]
            }
            await zb123.set_rule(uid, rule)
            return rule


class UserRuleApi(HTTPMethodView):
    def __init__(self):
        super().__init__()

    async def post(self, request: Request):
        """ 保存筛选规则 """
        uid = request.cookies.get('uid')
        assert uid

        # 保存筛选规则
        await zb123.set_rule(uid, request.json)

        return json_response({'success': True})


class SuggestApi(HTTPMethodView):
    """ 意见反馈 """
    async def post(self, request: Request):
        uid = request.cookies.get('uid')
        data = request.json
        await zb123.add_suggest(uid=uid, content=data['content'])
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
