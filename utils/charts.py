import json

from django.conf import settings
from django.http import HttpResponse
from example.commons import Faker
from pyecharts.charts import Line
from pyecharts import options as opts
from pymongo import MongoClient

from utils.tools import Calculator


def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


def get_term_point(score_dict):
    temp = {
        '学期_0': '大一上学期',
        '学期_1': '大一下学期',
        '学期_2': '大二上学期',
        '学期_3': '大二下学期',
        '学期_4': '大三上学期',
        '学期_5': '大三下学期',
        '学期_6': '大四上学期',
        '学期_7': '大四下学期'
    }
    result = dict()
    for k, v in score_dict.items():
        cal = Calculator()
        point = cal.average(v)
        result[temp[k]] = point
    return result


def charts(key) -> Line:
    client = MongoClient(settings.MG_HOST, settings.MG_PORT)
    db = client.jg
    terms = list(db[key].aggregate([{'$group': {'_id': '$学期'}}]))
    line_dict = dict()
    for i in range(len(terms)-1):
        term = '学期_' + str(i)
        scores = list(db[key].find({'学期': term}))
        line_dict[term] = scores
    result = get_term_point(line_dict)

    c = (
        Line()
            .add_xaxis([k for k, v in result.items()])
            .add_yaxis("绩点", [v for k,v in result.items()])
            .set_global_opts(title_opts=opts.TitleOpts(title="绩点折线图"))
            .dump_options()
    )
    return c
