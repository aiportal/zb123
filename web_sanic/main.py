import sanic
from sanic import Sanic, Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, json, redirect
from sanic.views import HTTPMethodView
from sanic.exceptions import InvalidUsage, NotFound, ServerError
import apis
from database import fetch, zb123, UserInfo, AccessLog, RuntimeEvent
import os


# 设置工作目录
os.chdir(os.path.dirname(os.path.realpath(__file__)))


app = Sanic(__name__)
app.static('/static', './static')


app.add_route(apis.WelcomeApi.as_view(), '/')
app.add_route(apis.WelcomeApi.as_view(), '/welcome')

api_wx = Blueprint('api_wx', url_prefix='/wx')
api_wx.add_route(apis.WxAuthApi.as_view(), '/auth')        # 微信认证
api_wx.add_route(apis.WxServiceApi.as_view(), '/svc')        # 微信服务后台
api_wx.add_route(apis.WxAccountsApi.as_view(), '/accounts')  # 微信账号
api_wx.add_route(apis.WxPublishApi.as_view(), '/publish')    # 每日发布
api_wx.add_route(apis.WxPublishApi.as_view(), '/preview')    # 每日发布
api_wx.add_route(apis.WxMenuApi.as_view(), '/menu')          # 微信菜单

api_v3 = Blueprint('api_v3', url_prefix='/api/v3')
api_v3.add_route(apis.UserInfoApi.as_view(), '/user')       # 用户信息
api_v3.add_route(apis.UserRuleApi.as_view(), '/rule')       # 筛选规则
api_v3.add_route(apis.SuggestApi.as_view(), '/suggest')     # 意见反馈
api_v3.add_route(apis.DayTitlesApi.as_view(), '/titles')    # 标题列表
api_v3.add_route(apis.ContentApi.as_view(), '/content/<uuid>', methods=['GET'])     # 详情信息
api_v3.add_route(apis.WxPayApi.as_view(), '/pay')            # 微信支付


async def valid_access(request: Request):
    """ 检查uid是否存在 """
    uid = request.cookies.get('uid')
    user = UserInfo.get_user(uid)
    if user:
        await zb123.log_access(uid, request.url, dict(request.headers, **{'ip': request.ip}))
    else:
        raise InvalidUsage('Invalid user.', status_code=403)


@api_v3.middleware('request')
async def on_request(request: Request):
    """ 验证访问权限 """
    url = request.url
    if url.startswith(api_v3.url_prefix):
        await valid_access(request)


@app.middleware('response')
async def on_response(request: Request, response: HTTPResponse):
    """ 确认UTF-8编码 """
    if request.url.startswith('/static'):
        response.content_type += '; charset=utf-8'
        response.headers['max-age'] = 24*60*60


@app.exception(NotFound, ServerError)
async def on_exception(request: Request, exception):
    """ 记录程序异常 """
    info = {'ip': request.ip, 'url': request.url, 'exception': str(exception)}
    await zb123.log_event('exception', info)


app.blueprint(api_wx)
app.blueprint(api_v3)


class AdminApi(sanic.views.HTTPMethodView):
    """ 管理员测试入口 """
    async def get(self, request: Request):
        resp = redirect('/welcome')
        resp.cookies['uid'] = 'o31RHuPslKvzzBccwwoXv_GKmfEA'
        return resp
app.add_route(AdminApi.as_view(), '/admin')


if __name__ == "__main__":
    if __debug__:
        app.run(host="0.0.0.0", port=88, debug=True)
    else:
        app.run(host="0.0.0.0", port=80, workers=4)
