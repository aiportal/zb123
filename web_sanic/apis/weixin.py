from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.response import text, json
from database import fetch, zb123, UserInfo
from weixin import wx_zb123, svc_zb123
from datetime import datetime, date


class WxServiceApi(HTTPMethodView):
    """ 微信服务后台 """
    # TODO: 使用request.headers['host']代替硬编码，从而支持多网址。（需要修改微信消息分发机制）
    web_host = 'zb123.ultragis.com'
    wx_app = wx_zb123
    wx_svc = svc_zb123

    def __init__(self):
        """ 定义要处理的微信消息类型 """
        self.wx_svc.events.subscribe = self.evt_subscribe
        self.wx_svc.events.unsubscribe = self.evt_unsubscribe
        self.wx_svc.messages.text = self.msg_text

    def get(self, request: Request):
        """ 微信服务回调 """
        echo = request.args.get('echostr')
        return text(echo)

    def post(self, request: Request):
        """ 微信消息处理 """
        res = self.wx_svc.process_message(request.args, request.body.decode())
        return text(res)

    def evt_subscribe(self, params):
        """ 用户关注消息"""

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
                    'PicUrl': 'http://{0}/img/handshake_600_275.png'.format(self.web_host),
                    'Url': 'http://{0}/static/help.html'.format(self.web_host)
                }]
            }
        }

    def evt_unsubscribe(self, params):
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


class WxPublishApi(HTTPMethodView):
    def __init__(self):
        self.wx_app = wx_zb123
        self.sources = []

    async def get(self, request: Request):
        if not self.sources:
            self.sources = {x.key: x.value for x in await zb123.get_config_items('source')}
        day = date.today()
        if 'day' in request.args:
            day = datetime.strptime(request.args.get('day'), '%Y%m%d').date()

        content = await self.totals_content(day)
        for oid in self.wx_app.admin:
            self.wx_app.preview_text(content, oid)

        return json({'success': True})

    async def totals_content(self, day: date):
        # 统计各省信息数量
        totals = await fetch.query_day_totals(day)

        # 标题
        amount = sum([v for _, v in totals.items()])
        headers = ['{0:%Y年%m月%d日}'.format(day), '各省共发布 {} 条招标信息'.format(amount), '']

        # 正文
        items = []
        for source in sorted(self.sources.keys()):
            alias = self.sources.get(source)
            total = totals.get(source, 0)
            items.append('{0}：{1} 条招标信息'.format(alias, total))
        footers = ['', '↓↓↓ 点击【招标信息】了解详情']

        return '\n'.join(headers + items + footers)


class WxMenuApi(HTTPMethodView):
    """ 初始化公众号菜单 """
    wx_app = wx_zb123

    def get(self, request: Request):
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
        return json({'success': True})
