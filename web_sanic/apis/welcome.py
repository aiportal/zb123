from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.response import redirect, json
from weixin import wx_zb123, wx_bayesian
from database import zb123, UserInfo
from datetime import datetime
import time


class WelcomeApi(HTTPMethodView):
    """ 网页入口 """
    url_auth = '/wx/auth'
    url_main = '/static/main.html'
    url_subscribe = '/static/zb123.html'

    def get(self, request: Request):
        # 检查Cookie
        uid = request.cookies.get('uid')
        if not uid:
            return redirect(self.url_auth)

        # 检查浏览器类型（只允许微信浏览器）
        agent = request.headers.get('user-agent', '')
        if __debug__ or 'micromessenger' in agent.lower():
            pass
        else:
            return redirect(self.url_auth)

        # 检查是否关注了订阅号
        user = UserInfo.get_user(uid)
        if user and user.zb123:
            return redirect(self.url_main)
        else:
            return redirect(self.url_subscribe)


class WxAuthApi(HTTPMethodView):
    """ 微信认证 """
    def __init__(self):
        self.auth_expires = 30*24*3600      # 认证过期时间（秒）
        self.wx_app = wx_bayesian           # 使用微信服务号进行认证

    def get(self, request: Request):
        """ 微信认证 """
        code = request.args.get('code')
        if not code:
            # 非回调，转向微信认证网址
            host = request.headers['host']
            url_callback = 'http://{0}{1}'.format(host, request.url)
            url = self.wx_app.oauth_url(url_callback, state=host)
            return redirect(url)
        else:
            # 微信回调，认证成功
            uid = self.request_unionid(code)
            host = request.args.get('state')

            # 转回入口网址
            if host:
                url = 'http://{0}{1}'.format(host, '/welcome')
            else:
                url = '/welcome'
            resp = redirect(url)

            # 设置 cookie，帮助 welcome 判断转向
            resp.cookies['uid'] = uid
            resp.cookies['uid']['expires'] = time.time() + self.auth_expires
            return resp

    def request_unionid(self, code: str) -> str:
        """ 获取用户的 unionid """
        # 用 code 换取服务号的 openid
        openid = self.wx_app.oauth_openid(code)

        # 用服务号的 openid 获取 uid
        uid = self.wx_app.user_info(openid).get('unionid')

        # 获取用户信息
        user = UserInfo.get_user(uid)
        if user and user.zb123:
            return uid
        else:
            # 下载用户信息到本地数据表
            WxAccountsApi.accounts_append(uid)
        return uid


class WxAccountsApi(HTTPMethodView):
    """ 微信账号同步 """
    wx_app = wx_zb123

    def get(self, request: Request):
        """ 下载并同步微信账号信息 """
        if 'uid' in request.args:
            errors = self.accounts_append(request.args.get('uid'))
        else:
            errors = self.accounts_update()
        return json(errors or {'success': True})

    @classmethod
    def accounts_update(cls):
        """ 更新本地存储的微信账号信息 """
        wx_app = cls.wx_app

        # 获取用户的 openid 列表
        keys = wx_app.user_list()

        # 去除黑名单用户
        blacks = wx_app.user_blacklist()
        keys = [x for x in keys if x not in blacks]

        errors = []
        for i in range(0, len(keys), 100):
            users = wx_app.user_batch(keys[i:i+100])
            users = sorted(users, key=lambda x: x['subscribe_time'])
            for user in users:
                try:
                    cls.account_add(user)
                except Exception as ex:
                    errors.append('{0}: {1}'.format(user['unionid'], str(ex)))
        return errors

    @classmethod
    def accounts_append(cls, uid=None):
        """ 添加微信账号信息到本地存储 """
        wx_app = cls.wx_app

        # 获取用户的 openid 列表
        keys = wx_app.user_list()

        # 去除黑名单用户
        blacks = wx_app.user_blacklist()
        keys = [x for x in keys if x not in blacks]

        # 去除已存在的用户
        query = UserInfo.select(UserInfo.zb123).where(UserInfo.uid != uid)
        keys = [x for x in keys if x not in [r.zb123 for r in query]]

        # 批量下载用户信息
        errors = []
        for i in range(0, len(keys), 100):
            users = wx_zb123.user_batch(keys[i:i+100])
            for user in users:
                if uid and uid != user['unionid']:
                    continue
                try:
                    cls.account_add(user)
                except Exception as ex:
                    errors.append(str(ex))
        return errors

    @classmethod
    def account_add(cls, user: dict) -> str:
        """ 添加微信账号 """

        # 先将utf8mb4的昵称暂存起来
        nickname = None
        if 'nickname' in user:
            nickname = user['nickname']
            del user['nickname']

        # 插入记录
        rec, is_new = UserInfo.get_or_create(uid=user['unionid'], defaults={
            'subscribe': str(datetime.fromtimestamp(user['subscribe_time']).date()),
            'info': user,
            'zb123': user['openid']
        })
        if not is_new:
            rec.info = user
            rec.zb123 = user['openid']
            rec.save()

        # 尝试保存utf8昵称
        if rec.nickname != nickname:
            try:
                rec.nickname = nickname
                rec.save()
            except Exception as ex:
                return str(ex)

        """ {'unionid': 'o31RHuAk-0ru02rBSupFDemh60SU',
             'groupid': 0,
             'sex': 1,
             'nickname': '秦嵩',
             'country': 'China',
             'subscribe_time': 1486292451,
             'tagid_list': [],
             'city': 'Taizhou',
             'remark': '',
             'language': 'zh_CN',
             'province': 'Zhejiang',
             'openid': 'o3cwBvwbfqL3DMdALBiSGk-j6pvM',
             'headimgurl': 'http://wx.qlogo.cn/mmopen/PiajxSqBRaELpAPhP3PQbDrbHLVJ1eacbP5W7FAujZdBbicAsf6pfdoOGic0LUXBxdRfibicbZS6cpBNPflEPV9UV1g/0',
             'subscribe': 1
        } """
