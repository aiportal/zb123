from .app import WxAppCore
from urllib import parse


class WxOAuthManager(WxAppCore):
    def oauth_url(self, redirect_uri, state=None, scope='snsapi_base'):
        """ 微信认证网址 """
        oauth_url = 'https://open.weixin.qq.com/connect/oauth2/authorize' \
                    '?appid={0}' \
                    '&{1}' \
                    '&response_type=code' \
                    '&scope={2}' \
                    '&state={3}' \
                    '#wechat_redirect'
        redirect_param = parse.urlencode({'redirect_uri': redirect_uri})
        url = oauth_url.format(self.app_id, redirect_param, scope, state)
        return url

    def oauth_openid(self, code):
        """ 获取用户的openid """
        oauth_token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token'
        params = {
            'appid': self.app_id,
            'secret': self.secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
        return self.get(oauth_token_url, params)['openid']
