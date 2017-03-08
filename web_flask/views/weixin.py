from flask.views import MethodView, request
from .core import json_response, text_response
from database import GatherInfo, UserInfo, SysConfig
from peewee import fn
from weixin import wx_zb123, svc_zb123
from datetime import datetime, date, timedelta


class WxServiceApi(MethodView):
    """ 微信服务后台 """
    wx_app = wx_zb123
    wx_svc = svc_zb123

    def __init__(self):
        """ 定义要处理的微信消息类型 """
        self.wx_svc.events.subscribe = self.evt_subscribe
        self.wx_svc.events.unsubscribe = self.evt_unsubscribe
        self.wx_svc.messages.text = self.msg_text

    @property
    def web_host(self):
        return request.host

    def get(self):
        """ 微信服务回调 """
        echo = request.args.get('echostr')
        return text_response(echo)

    def post(self):
        """ 微信消息处理 """
        res = self.wx_svc.process_message(request.args, request.get_data(as_text=True))
        return text_response(res)

    def evt_subscribe(self, params):
        """ 用户关注消息 """
        # 回复一条链接消息，让用户第一时间打开主页
        return {
            'ToUserName': params['FromUserName'],
            'FromUserName': params['ToUserName'],
            'CreateTime': int(datetime.now().timestamp()),
            'MsgType': 'news',
            'ArticleCount': 1,
            'Articles': {
                'item': [{
                    'Title': '招标信息',
                    'Description': '欢迎订阅招标123，招标信息一网打尽。',
                    'PicUrl': 'http://{0}/static/img/handshake_600_275.png'.format(self.web_host),
                    'Url': 'http://{0}/static/help.html'.format(self.web_host)
                }]
            }
        }

    def evt_unsubscribe(self, params):
        """ 用户取消关注 """
        query = UserInfo.update(zb123=None).where(UserInfo.zb123 == params['FromUserName'])
        query.execute()

    def msg_text(self, params):
        content = params['Content']     # type: str

        # 执行操作指令
        if content.startswith('*#') and content.endswith('#*'):
            name = 'cmd_' + content.strip('*#')
            handler = hasattr(self, name) and getattr(self, name) or None
            return handler and handler(params) or None

        return {
            'ToUserName': params['FromUserName'],
            'FromUserName': params['ToUserName'],
            'CreateTime': int(datetime.now().timestamp()),
            'MsgType': 'text',
            'Content': '感谢您关注【招标123】\n如有问题或建议，请使用【意见反馈】菜单提交。'
        }


class WxPublishApi(MethodView):
    def __init__(self):
        self.wx_app = wx_zb123
        self.sources = {x.key: x.value for x in SysConfig.get_items('source')}

    def get(self):
        """ 全网发布或预览 """
        day = request.args.get('day') and datetime.strptime(request.args.get('day'), '%Y%m%d').date() or date.today()

        # 组织发布内容
        content = self.totals_content(day)

        # 发布或预览
        if request.path.endswith('/publish'):
            self.wx_app.publish_text(content)
        else:
            for oid in self.wx_app.admin:
                self.wx_app.preview_text(content, oid)

        return json_response({
            'success': True,
            'content': content
        })

    def totals_content(self, day: date):
        # 统计各省信息数量
        day = day - timedelta(1)
        totals = self.query_day_totals(day)

        # 标题
        amount = sum([v for _, v in totals.items()])
        headers = ['昨日各省共发布 {} 条招标信息'.format(amount), '']

        # 正文
        items = []
        for source in sorted(totals, key=totals.get, reverse=True):
            alias = self.sources.get(source)
            total = totals.get(source, 0)
            items.append('{0}：{1} 条招标信息'.format(alias, total))
        footers = ['', '↓↓↓ 点击【招标信息】了解详情']

        return '\n'.join(headers + items + footers)

    @staticmethod
    def query_day_totals(day: date) -> dict:
        query = GatherInfo.select(GatherInfo.source, fn.Count(GatherInfo.uuid).alias('count'))\
            .where(GatherInfo.day == str(day))\
            .group_by(GatherInfo.source)
        return {x.source: x.count for x in query}


class WxMenuApi(MethodView):
    """ 初始化公众号菜单 """
    wx_app = wx_zb123

    def get(self):
        url_menu_create = 'https://api.weixin.qq.com/cgi-bin/menu/create'
        host = request.headers['host']
        data = {
            "button": [{
                "type": "view",
                "name": "招标信息",
                "url": "http://{0}/welcome".format(host)
            }, {
                "type": "view",
                "name": "推荐关注",
                "url": "http://{0}/static/zb123.html".format(host)
            }, {
                "type": "view",
                "name": "意见反馈",
                "url": "http://{0}/static/suggest.html".format(host)
            }]
        }
        self.wx_app.post(url_menu_create, data)
        return json_response({
            'success': True,
            'menu': data
        })
