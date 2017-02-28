from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.exceptions import ServerError
from .core import xml_response
from database import zb123, AnnualFee
from weixin import wx_bayesian
from datetime import datetime, date
import uuid, requests, qrcode, io, hashlib, xmltodict


class WxPayApi(HTTPMethodView):
    """ 微信支付 """
    app_id = wx_bayesian.app_id
    mch_id = '1242232502'       # 商户号
    mch_key = '1EA06758BC1911E6965C08D40CCA2C3C'
    # server_ip = '120.76.129.87'
    server_ip = '101.201.234.182'

    def get(self, request: Request):
        """ 生成订单二维码 """

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid and len(uid) > 10

        # 支付金额
        fee = int(request.args.get('fee', 300))
        if uid == 'o31RHuPslKvzzBccwwoXv_GKmfEA':
            fee = 1

        # 生成支付网址
        order_url = self.make_order_url(fee, '招标123-VIP会员', request.url, uid)

        # 返回二维码图片
        img = qrcode.make(order_url, border=2)
        bs = io.BytesIO()
        img.save(bs, 'png')
        return HTTPResponse(content_type='image/png', body_bytes=bs.getvalue())

    def make_order_url(self, fee: int, title: str, url: str, uid: str) -> str:
        """ 生成订单网址 """

        # 构造订单参数
        nonce_str = str(uuid.uuid1()).replace('-', '')      # 随机字符串
        order_id = '{0:%Y%m%d%H%M%S}00{1}'.format(datetime.now(), uid[-6:])     # 自定义的订单编号
        url_callback = 'http://{0}{1}'.format(self.server_ip, url)              # 支付成功的回调网址
        order_params = {
            'appid': self.app_id,                   # 公众账号ID
            'mch_id': self.mch_id,                  # 商户号
            'trade_type': 'NATIVE',                 # 交易类型
            'spbill_create_ip': self.server_ip,     # APP和网页支付提交用户端ip，Native支付填调用微信支付API的机器IP。
            'notify_url': url_callback,             # 异步接收微信支付结果通知的回调地址
            'nonce_str': nonce_str,                 # 随机字符串（长度要求在32位以内）
            'body': title,                          # 商品描述（该字段请按照规范传递，具体请见参数规定）
            'product_id': 'zb123',                  # 产品ID
            'out_trade_no': order_id,               # 商户订单号（商户系统内部订单号，要求32个字符内、且在同一个商户号下唯一）
            'total_fee': fee * 100,                 # 订单总金额，单位为分
            'attach': uid,                          # 附加信息（用户UID）
        }
        order_params['sign'] = self.sign_order_params(order_params)

        # 生成订单链接
        url_wx_order = 'https://api.mch.weixin.qq.com/pay/unifiedorder'     # 生成微信订单的网址
        try:
            xml = xmltodict.unparse({'xml': order_params})
            resp = requests.post(url_wx_order, data=xml.encode(), headers={})
            res = xmltodict.parse(resp.content.decode())['xml']
            if res['return_code'] == 'SUCCESS' and res['result_code'] == 'SUCCESS':
                return res['code_url']
            else:
                raise ServerError('pay order error: ' + res.get('err_code_des'))
        except Exception as ex:
            raise ServerError('pay order exception: ' + str(ex))

    async def post(self, request: Request):
        """ 微信支付回调 """
        xml = request.body.decode()
        data = xmltodict.parse(xml)['xml']

        # 检查支付状态
        if data['sign'] != self.sign_order_params(data):
            raise ServerError('pay sign invalid: ' + str(data))
        if data['return_code'] != 'SUCCESS' or data['result_code'] != 'SUCCESS':
            raise ServerError('pay return fail: ' + str(data))

        # 记录订单信息
        uid = data['attach']
        orders = await zb123.get_orders(uid)
        if not any(x.order_id == data['transaction_id'] for x in orders):
            start = orders[0].end if len(orders) > 0 else date.today()
            end = start.replace(start.year + 1)
            rec = AnnualFee(**{
                'uid': uid,
                'day': date.today(),
                'start': start,
                'end': end,
                'amount': int(data['total_fee']) / 100,
                'order_no': data['out_trade_no'],
                'order_id': data['transaction_id'],
            })
            rec.save()

        # 返回
        result = {'return_code': 'SUCCESS', 'return_msg': 'OK'}
        return xml_response({'xml': result})

    def sign_order_params(self, params: dict):
        """ 获取参数签名 """
        sign_str = '&'.join(['{0}={1}'.format(k, params[k])
                             for k in sorted(params.keys())
                             if params[k] and k != 'sign'])
        sign_str += '&key=' + self.mch_key
        return hashlib.md5(sign_str.encode()).hexdigest().upper()
