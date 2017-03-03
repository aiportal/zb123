import sanic
from sanic import Sanic, Blueprint
from sanic.request import Request
from sanic.response import HTTPResponse, json, text, redirect
from sanic.exceptions import SanicException, InvalidUsage, NotFound, ServerError, RequestTimeout
from sanic.handlers import ErrorHandler
import apis
from database import db_fetch, db_zb123, fetch, zb123, UserInfo, AccessLog, RuntimeEvent
import os


# change work dir
os.chdir(os.path.dirname(os.path.realpath(__file__)))


class GlobalErrorHandler(ErrorHandler):
    def default(self, request, exception):
        info = {'ip': request.ip, 'url': request.url, 'exception': str(exception)}
        RuntimeEvent.log_event('error', info)
        return super().default(request, exception)


app = Sanic(__name__, error_handler=GlobalErrorHandler())
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
api_v3.add_route(apis.ContentApi.as_view(), '/content/<uuid>')     # 详情信息
api_v3.add_route(apis.WxPayApi.as_view(), '/pay')            # 微信支付


# check api request
@api_v3.middleware('request')
async def on_api_request(request: Request):
    url = request.url
    if url.startswith(api_v3.url_prefix):
        # 检查uid是否存在
        uid = request.cookies.get('uid')
        user = UserInfo.get_user(uid)
        if user:
            await zb123.log_access(uid, request.url, dict(request.headers, **{'ip': request.ip}))
        else:
            return text('Invalid usage.', status=403)


# cache static file
@app.middleware('response')
async def on_response(request: Request, response: HTTPResponse):
    """ 确认UTF-8编码 """
    if request.url.startswith('/static'):
        response.content_type += '; charset=utf-8'
        response.headers['max-age'] = 24*60*60


# log exceptions
@app.exception(NotFound, ServerError, RequestTimeout)
async def on_exception(request: Request, exception: SanicException):
    """ 记录程序异常 """
    info = {'ip': request.ip, 'url': request.url, 'exception': str(exception)}
    await zb123.log_event('exception', info)
    return text('error', status=exception.status_code)


# valid sync database connection
@app.middleware('request')
def on_request_db(request: Request):
    """ 确认数据库连接 """
    if db_fetch.is_closed():
        db_fetch.connect()
    if db_zb123.is_closed():
        db_zb123.connect()


# @app.middleware('response')
# def on_response_db(request: Request, response: HTTPResponse):
#     db_fetch.close()
#     db_zb123.close()


app.blueprint(api_wx)
app.blueprint(api_v3)

if __name__ == "__main__":

    from sanic.views import HTTPMethodView


    class AdminApi(HTTPMethodView):
        """ 管理员测试入口 """
        async def get(self, request: Request):
            resp = redirect('/static/main.html')
            resp.cookies['uid'] = 'o31RHuPslKvzzBccwwoXv_GKmfEA'
            return resp
    app.add_route(AdminApi.as_view(), '/admin')

    if __debug__:
        app.run(host="0.0.0.0", port=88, debug=True)
    else:
        app.run(host="0.0.0.0", port=80, workers=4)
