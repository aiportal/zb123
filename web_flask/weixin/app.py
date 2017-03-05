from database import SysConfig
from datetime import datetime, timedelta
import requests
import json


class WxError(RuntimeError):
    @classmethod
    def check(cls, res: dict):
        if 'errcode' in res and res['errcode'] > 0:
            err = cls('wx error: {0} {1}'.format(res.get('errcode'), res.get('errmsg')))
            err.__dict__.update(res)
            raise err
        else:
            return res


class WxAccessToken:
    __time = datetime.now()             # 更新时间
    __expire = timedelta(seconds=0)     # 过期时间
    __value = None                      # Token值

    def __new__(cls, app_id: str, token_url: str):
        """ 实现基于app_id的单例模式 """
        if not hasattr(cls, '__tokens'):
            setattr(cls, '__tokens', {})
        tokens = getattr(cls, '__tokens')
        if app_id not in tokens:
            self = super().__new__(cls)
            self.url = token_url
            tokens[app_id] = self
        return tokens[app_id]

    def update(self):
        try:
            res = requests.get(self.url).json()
        except Exception as ex:
            raise ex
        res = WxError.check(res)
        self.__time = datetime.now()
        self.__expire = timedelta(0, 7000)
        self.__value = res['access_token']

    @property
    def value(self):
        if (self.__time + self.__expire) < datetime.now():
            self.update()
        return self.__value


class WxAppCore:
    # _wx_access_token_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}'

    def __init__(self, app_id: str, secret: str):
        self.__app_id = app_id
        self.__secret = secret
        # token_url = self._wx_access_token_url.format(app_id, secret)
        # self._token = WxAccessToken(app_id, token_url)

    @property
    def app_id(self):
        return self.__app_id

    @property
    def secret(self):
        return self.__secret

    @property
    def access_token(self):
        # return self._token.value
        return self.get_access_token()

    def get(self, url: str, params: dict = None):
        params = params or {}
        if 'access_token' not in params:
            params['access_token'] = self.access_token
        res = requests.get(url, params).json()
        return self.check_result(res)

    def post(self, url: str, data: dict = None):
        url = '{0}{2}access_token={1}'.format(url, self.access_token, ('?' in url and '&' or '?'))
        body = json.dumps(data, ensure_ascii=False).encode()
        res = requests.post(url, body).json()
        return self.check_result(res)

    def upload(self, url: str, files: dict):
        url = '{0}{2}access_token={1}'.format(url, self.access_token, ('?' in url and '&' or '?'))
        res = requests.post(url, files=files).json()
        return self.check_result(res)

    def check_result(self, res):
        # 如果是 access_token 无效，强制更新
        if res.get('errcode') == 40001:
            self.get_access_token(True)
        return WxError.check(res)

    def get_access_token(self, force_update=False):
        """ 获取或更新数据库中保存的AccessToken """
        token = SysConfig.get_item('WxAccessToken', self.app_id)
        expire = datetime.fromtimestamp(int(token.info or '0'))

        # 未过期，直接返回
        if not force_update:
            if datetime.now() < expire:
                return token.value

        # 已过期，更新AccessToken
        # 首先修改过期时间, 避免其他进程同时更新
        expire = datetime.now() + timedelta(seconds=30)     # 锁定30秒
        token.info = int(expire.timestamp())
        token.save()

        # 请求并更新access_token
        try:
            # 获取
            url_token = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}'
            url = url_token.format(self.app_id, self.secret)
            res = requests.get(url).json()
            res = WxError.check(res)
            # 保存
            expire = datetime.now() + timedelta(seconds=7000)
            token.value = res['access_token']
            token.info = int(expire.timestamp())
            token.save()
        except Exception as ex:
            raise ex
        finally:
            return token.value
