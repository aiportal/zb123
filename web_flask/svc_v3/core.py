from flask import request, Response, send_file
from flask.views import MethodView as HTTPMethodView
import json
import xmltodict
import io


def text_response(body: str, headers=None):
    return Response(body, content_type='text/plain', headers=headers)


def json_response(body: dict, headers=None):
    """ 返回json """
    data = json.dumps(body, ensure_ascii=False, sort_keys=True)
    return Response(data, content_type='application/json', headers=headers)


def xml_response(body: dict, headers=None):
    """ 返回xml """
    data = xmltodict.unparse(body)
    return Response(data, content_type='text/xml', headers=headers)


def send_image(image, cache_timeout=0):
    """ 返回image """
    bs = io.BytesIO()
    image.save(bs, 'png')
    bs.seek(0)
    return send_file(bs, mimetype='image/png', cache_timeout=cache_timeout)


class ServerError(Exception):
    pass
