from flask import request, Response, send_file
from flask.views import MethodView as HTTPMethodView
import json
import xmltodict
import io


def json_response(body: dict, headers=None):
    """ 返回json """
    data = json.dumps(body, ensure_ascii=False, sort_keys=True)
    return Response(data, content_type='application/json', headers=headers)


def xml_response(body: dict, headers=None):
    """ 返回xml """
    data = xmltodict.unparse(body)
    return Response(data, content_type='text/xml', headers=headers)


class ServerError(Exception):
    pass
