from flask import Flask, Blueprint, request, make_response, redirect, url_for
#from flask_restful import Api, output_json
import svc_v3
from api_v3 import api_v3
from api_v3_1 import api_v3_1
from api_v4 import api_v4
from cmd_v3 import cmd_v3

from database import Database, UserInfo, AccessLog, RuntimeEvent


app = Flask(__name__)
app.config['RESTFUL_JSON'] = {'ensure_ascii': False}


@app.before_request
def before_req():
    Database.connect()


@app.teardown_request
def teardown_request(exc):
    try:
        AccessLog.log_access(request.cookies.get('uid'), request.url, {'ip': request.remote_addr, 'ex': str(exc)})
    except Exception as ex:
        print('<<< teardown_req >>> ', ex)
    Database.close()
    # gevent.spawn(after, request.cookies.get('uid'), request.url, request.remote_addr)


@app.errorhandler
def log_exception(e):
    RuntimeEvent.log_event(level='error', info={'exception': str(e)})


@app.route('/')
def hello_world():
    return 'Hello zb123!'

# static to root
root = Blueprint('static', 'static', static_folder='static', static_url_path='', url_prefix='')
app.register_blueprint(root)


app.add_url_rule('/welcome', view_func=svc_v3.WelcomeApi.as_view('welcome'))                 # 网页入口
app.add_url_rule('/wx/auth', view_func=svc_v3.WxAuthApi.as_view('auth'))                     # 微信认证服务
app.add_url_rule('/wx/pay', view_func=svc_v3.WxPayApi.as_view('pay'))                        # 微信支付
app.add_url_rule('/wx/accounts', view_func=svc_v3.WxAccountsApi.as_view('accounts'))         # 微信账号同步
app.add_url_rule('/wx/svc', view_func=svc_v3.WxServiceApi.as_view('svc'))                    # 微信公众号消息服务
app.add_url_rule('/wx/publish', view_func=svc_v3.WxPublishApi.as_view('publish'))            # 微信每日推送/预览
app.add_url_rule('/wx/sendall', view_func=svc_v3.WxPublishApi.as_view('sendall'))            # 微信每日推送/预览
app.add_url_rule('/wx/preview', view_func=svc_v3.WxPublishApi.as_view('preview'))
app.add_url_rule('/wx/menu', view_func=svc_v3.WxMenuApi.as_view('menu'))                     # 初始化微信菜单

# 注册API接口
app.register_blueprint(api_v3)
app.register_blueprint(api_v3_1)
app.register_blueprint(api_v4)

# 注册Web指令
app.register_blueprint(cmd_v3)

# 注册新版服务
# app.register_blueprint(svc_v4)


# 调试
@app.route('/debug')
def debug():
    resp = make_response(redirect(url_for('welcome', _external=True)))
    # 设置 cookie，帮助 welcome 网址判断转向
    uid = request.args.get('uid', 'o31RHuPslKvzzBccwwoXv_GKmfEA')
    resp.set_cookie('uid', value=uid)
    return resp


if __name__ == '__main__':
    from gevent.wsgi import WSGIServer
    from werkzeug.serving import run_with_reloader
    from werkzeug.debug import DebuggedApplication

    @run_with_reloader
    def run_server():
        http_server = WSGIServer(('0.0.0.0', 81), DebuggedApplication(app))
        http_server.serve_forever()
    run_server()

