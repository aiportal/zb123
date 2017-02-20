from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.response import text, json
from peewee import fn
from database import UserInfo, GatherInfo, SysConfig
from weixin import wx_zb123, svc_zb123
from datetime import datetime, date


class WxServiceApi(HTTPMethodView):
    """ 微信服务后台 """
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
                    'PicUrl': 'http://zb.ultragis.com/img/handshake_600_275.png',
                    'Url': 'http://zb.ultragis.com/help.html'
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
    """ 招标信息发布 """
    def __init__(self):
        self.author = '招标123'
        self.welcome_url = 'zb.ultragis.com/welcome'
        self.cover_image = 'B3VHJYoCxJUobp6S3huJ8USM524lDTDizaWMYhgMCSo'
        self.preview_users = ['o3cwBvzJe_vrBtOc2P3AUBS1wbEM', 'o3cwBv-nFc2bwfPjJL4O--34PbX8']
        self.wx_app = wx_zb123
        self.sources = {x.key: x.value for x in SysConfig.get_items('source')}

    def get(self, request: Request):
        day = date.today()
        if 'day' in request.args:
            day = datetime.strptime(request.args['day'], '%Y%m%d').date()
        archive = self.totals_archive(day)
        media_id = self.wx_app.add_news(archive)

        preview = request.url.strip('/').endswith('preview')
        if preview:
            for openid in self.preview_users:
                self.wx_app.preview_news(media_id=media_id, openid=openid)
        else:
            self.wx_app.publish_news(media_id=media_id)
        return json({'success': True})

    def totals_archive(self, day):
        # 统计各省信息数量
        records = (GatherInfo.select(GatherInfo.source, fn.Count(GatherInfo.uuid).alias('count'))
                   .where(GatherInfo.day == str(day))
                   .group_by(GatherInfo.source))
        totals = {x.source: x.count for x in records}

        # 标题
        title = '{0:%Y-%m-%d} 招标信息'.format(day)

        # 正文
        items = []
        for source in sorted(self.sources.keys()):
            alias = self.sources.get(source)
            total = totals.get(source, 0)
            items.append('<p><b>{0}：</b>&nbsp;<span>{1}</span>条招标信息</p>'.format(alias, total))
        content = ''.join(items)
        content += '<br/><p><strong style="color:rgb(255,79,121);">↓↓↓</strong>&nbsp;请点击“阅读原文”了解详细信息</p>'

        # 摘要
        amount = sum([v for _, v in totals.items()])
        digest = '今日共发布 {0} 条招标信息'.format(amount)

        return self.wx_app.article(title=title, content=content, digest=digest, url=self.welcome_url,
                                   author=self.author, image_id=self.cover_image)


class WxMenuApi(HTTPMethodView):
    """ 初始化公众号菜单 """
    wx_app = wx_zb123

    def get(self):
        url_menu_create = 'https://api.weixin.qq.com/cgi-bin/menu/create'
        data = {
            "button": [{
                "type": "view",
                "name": "招标信息",
                "url": "http://zb.ultragis.com/welcome"
            }, {
                "type": "view",
                "name": "推荐关注",
                "url": "http://zb.ultragis.com/zb123.html"
            }, {
                "type": "view",
                "name": "意见反馈",
                "url": "http://zb.ultragis.com/suggest.html"
            }]
        }
        self.wx_app.post(url_menu_create, data)
        return json({'success': True})
