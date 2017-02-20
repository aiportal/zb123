from hashlib import sha1
import xmltodict
import logging


class WxAppEvents:
    """ 事件 """
    subscribe = None    # type: Callable | None
    unsubscribe = None  # type: Callable | None
    scan = None         # type: Callable | None
    location = None     # type: Callable | None
    click = None        # type: Callable | None
    view = None         # type: Callable | None


class WxAppMessages:
    """ 消息 """
    text = None         # type: Callable | None
    image = None        # type: Callable | None
    voice = None        # type: Callable | None
    video = None        # type: Callable | None
    shortvideo = None   # type: Callable | None
    location = None     # type: Callable | None
    link = None         # type: Callable | None


class WxAppService:
    """
     :type events: WxAppEvents
     :type messages: WxAppMessages
    """
    events = property(lambda self: self._events)
    messages = property(lambda self: self._messages)

    def __init__(self, app_id: str, token: str, aes_key: str):
        """ 微信消息服务
        :param app_id: 公众号的appid
        :param token: 令牌
        :param aes_key: 消息加解密密钥
        """
        self._app_id = app_id
        self._token = token
        self._aes_key = aes_key
        self._events = WxAppEvents()
        self._messages = WxAppMessages()
        self.log = logging.getLogger('WxAppService')

    def check_signature(self, args: dict) -> bool:
        """ 验证消息来自微信服务器 """
        if __debug__:
            return True
        value = ''.join(sorted([args['timestamp'], args['nonce'], self._token]))
        sign = sha1(value.encode()).hexdigest()
        return sign == args['signature']

    def process_message(self, args: dict, body: str) -> str:
        """ 微信消息处理 """
        if not self.check_signature(args):
            return None

        #################################
        # 此处解密消息体
        ################################
        params = {k: v for k, v in xmltodict.parse(body)['xml'].items()}
        data = self.dispatch_message(params)
        if data and isinstance(data, dict):
            result = xmltodict.unparse({'xml': data})
            #######################################
            # 此处加密消息体
            #######################################
            return result
        else:
            return 'success'

    def dispatch_message(self, params: dict) -> dict:
        msg = params['MsgType'].lower()
        if msg == 'event':
            evt = params['Event'].lower()
            handler = hasattr(self.events, evt) and getattr(self.events, evt) or None
        else:
            handler = hasattr(self.messages, msg) and getattr(self.messages, msg) or None
        try:
            if callable(handler):
                return handler(params)
        except Exception as ex:
            self.log.error(str(ex))
