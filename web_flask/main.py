from flask import Flask, Blueprint, request, make_response, redirect, url_for
#from flask_restful import Api, output_json
import apis
import views
from cmds import cmd_v3
from database import Database, UserInfo, AccessLog, RuntimeEvent


app = Flask(__name__)
app.config['RESTFUL_JSON'] = {'ensure_ascii': False}


@app.before_request
def before_req():
    Database.connect()


@app.teardown_request
def teardown_req(exc):
    try:
        uid = request.cookies.get('uid', '')
        AccessLog.log_access(uid, request.url, {'ip': request.remote_addr, 'host': request.host, 'root': request.host_url})
    except Exception as ex:
        print('<<< teardown_req >>> ', str(ex))
    Database.close()


@app.errorhandler
def log_exception(e):
    RuntimeEvent.log_event(level='error', info={'exception': str(e)})


@app.route('/')
def hello_world():
    return 'Hello zb123!'

# static to root
root = Blueprint('static', 'static', static_folder='static', static_url_path='', url_prefix='')
app.register_blueprint(root)


app.add_url_rule('/welcome', view_func=views.WelcomeApi.as_view('welcome'))                 # 网页入口
app.add_url_rule('/wx/auth', view_func=views.WxAuthApi.as_view('auth'))                     # 微信认证服务
app.add_url_rule('/wx/pay', view_func=views.WxPayApi.as_view('pay'))                        # 微信支付
app.add_url_rule('/wx/accounts', view_func=views.WxAccountsApi.as_view('accounts'))         # 微信账号同步
app.add_url_rule('/wx/svc', view_func=views.WxServiceApi.as_view('svc'))                    # 微信公众号消息服务
app.add_url_rule('/wx/publish', view_func=views.WxPublishApi.as_view('publish'))            # 微信每日推送/预览
app.add_url_rule('/wx/sendall', view_func=views.WxPublishApi.as_view('sendall'))            # 微信每日推送/预览
app.add_url_rule('/wx/preview', view_func=views.WxPublishApi.as_view('preview'))
app.add_url_rule('/wx/menu', view_func=views.WxMenuApi.as_view('menu'))                     # 初始化微信菜单

# API接口
api_v3 = Blueprint('api_v3', 'api_v3', url_prefix='/api/v3')
api_v3.add_url_rule('/user', view_func=apis.UserInfoApi.as_view('user'))                    # 用户界面初始化
api_v3.add_url_rule('/rule', view_func=apis.UserRuleApi.as_view('rule'))                    # 设置筛选规则
api_v3.add_url_rule('/titles', view_func=apis.DayTitlesApi.as_view('titles'))               # 获取招标信息
api_v3.add_url_rule('/content/<uuid>', view_func=apis.ContentApi.as_view('content'))        # 招标信息详情
api_v3.add_url_rule('/suggest', view_func=apis.SuggestApi.as_view('suggest'))               # 意见反馈


@api_v3.before_request
def before_api_request():
    """ 检查访问权限 """
    Database.connect()
    uid = request.cookies.get('uid')
    user = UserInfo.get_user(uid)
    if not user:
        return make_response('Invalid usage.')

# 注册API接口
app.register_blueprint(api_v3)

# 注册Web指令
app.register_blueprint(cmd_v3)


# 调试
@app.route('/debug')
def debug():
    resp = make_response(redirect(url_for('welcome', _external=True)))
    # 设置 cookie，帮助 welcome 网址判断转向
    uid = request.args.get('uid', 'o31RHuPslKvzzBccwwoXv_GKmfEA')
    resp.set_cookie('uid', value=uid)
    return resp


if __name__ == '__main__':
    if __debug__:
        app.run('0.0.0.0', 81, debug=True)
    else:
        app.run('0.0.0.0', 80, debug=False)

