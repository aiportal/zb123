from sanic import Sanic, Blueprint
from sanic.request import Request
from apis import *
from database import AccessLog, RuntimeEvent
from sanic.response import json, HTTPResponse
from sanic.views import HTTPMethodView
from database import zb123
from datetime import datetime

app = Sanic(__name__)
app.static('/', './static')

app.add_route(WelcomeApi().as_view(), '/')
app.add_route(WelcomeApi().as_view(), '/welcome')

api_wx = Blueprint('api_wx', url_prefix='/wx')
api_wx.add_route(WxAuthApi().as_view(), '/auth')        # 微信认证
api_wx.add_route(WxAccountsApi.as_view(), '/accounts')  # 微信账号
api_wx.add_route(WxPayApi.as_view(), '/pay')            # 微信支付
api_wx.add_route(WxServiceApi.as_view(), '/svc')        # 微信服务后台
api_wx.add_route(WxPublishApi.as_view(), '/publish')    # 每日发布
api_wx.add_route(WxPublishApi.as_view(), '/preview')    # 每日发布
api_wx.add_route(WxMenuApi.as_view(), '/menu')          # 微信菜单
app.blueprint(api_wx)

api_v3 = Blueprint('api_v3', url_prefix='/api/v3')
api_v3.add_route(UserInfoApi.as_view(), '/user')       # 用户信息
api_v3.add_route(UserRuleApi.as_view(), '/rule')       # 筛选规则
api_v3.add_route(SuggestApi.as_view(), '/suggest')     # 意见反馈
api_v3.add_route(DayTitlesApi.as_view(), '/titles')    # 标题列表
api_v3.add_route(ContentApi.as_view(), '/content/<uuid>', methods=['GET'])     # 详情信息
app.blueprint(api_v3)


@app.route('/post/<key>/<value>')
async def post(request, key, value):
    await zb123.create(AccessLog, uid=key, url=request.url, info=value)
    return json({'success': True})


@app.middleware('request')
async def on_request(request: Request):
    print('[{0}] {1} {2}'.format(str(datetime.now()), request.url, request.cookies.get('uid')))
#     uid = request.cookies.get('uid')
#     url = request.url
#     info = {}
#     await AccessLog.log_access(uid, url, info)
#     print('after request')
#     # print("I print when a request is received by the server")


# @api_v3.middleware('response')
# async def on_response(request, response):
#     pass
    # print(request.url)


@app.exception
async def on_exception(request: Request, exception):
    data = {'url': request.url, 'exception': str(exception)}
    RuntimeEvent.log_event('exception', str(data))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
