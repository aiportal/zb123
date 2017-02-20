from sanic.response import HTTPResponse, json_dumps
import xmltodict


def json_response(body, status=200, headers=None, **kwargs):
    """ 返回json """
    kwargs.update({'ensure_ascii': False})
    return HTTPResponse(json_dumps(body, **kwargs), headers=headers,
                        status=status, content_type="application/json")


def xml_response(body, status=200, headers=None, **kwargs):
    return HTTPResponse(xmltodict.unparse(body, **kwargs), headers=headers,
                        status=status, content_type='text/xml')
