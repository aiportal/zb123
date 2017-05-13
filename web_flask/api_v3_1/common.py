from flask.views import MethodView
from flask import request, Response, send_file
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


def image_response(image, img_type: str='png', cache_timeout: int=0):
    """ 返回image """
    with io.BytesIO() as bs:
        image.save(bs, img_type)
        bs.seek(0)
        return send_file(bs, mimetype='image/' + img_type, cache_timeout=cache_timeout)


class ServerError(Exception):
    pass
