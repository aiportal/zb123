from .app import WxAppCore, WxError
from .user import WxUserManager
from .oauth import WxOAuthManager
from .service import WxAppService
from .news import WxMediaManager, WxNewsManager
from .custom import WxCustomManager


class WxAppProxy(WxUserManager, WxOAuthManager, WxMediaManager, WxNewsManager, WxCustomManager):
    def __init__(self, app_id, secret):
        super().__init__(app_id, secret)


wx_zb123 = WxAppProxy('wx771e2cc7f5351ad1', '551443ec00095e52547c3c7867e47aff')
wx_bayesian = WxAppProxy('wxbe695f1392c7fdf8', '1c2be20b0f30fd71bf4d84557578ff7a')


svc_zb123 = WxAppService('wx771e2cc7f5351ad1', 'zb123', 'VNgbVPZjcaLEIaHac9YApEgxG4TlqzTOtgPAr32RS6i')
svc_bayesian = WxAppService('wxbe695f1392c7fdf8', 'bayesian', 'VlOZCtqBlhWRbTZGCuwkYlUycvlVd9FgaCAqNuFQLuX')

wx_zb123.admin = ['o3cwBvzJe_vrBtOc2P3AUBS1wbEM']