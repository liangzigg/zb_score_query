import os

import django
import requests
from celery import Celery
from lxml import etree
from retry import retry

from utils.tools import Processor


# 配置django环境
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "score_analysis.settings")
django.setup()

from django.conf import settings

""" 启动celery
    celery -A celery_tasks.tasks worker -l info
    -A 指定 app对象所在模块
    -l 指定输出级别为 info
"""

# 创建celery 对象
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/5')


HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Host': '202.207.177.39:8089',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
}


# 调用方法 get_cookies.delay(username, password)  # celery异步调用
@app.task
@retry(tries=3)
def get_jg_score(username, cookies):
    """查询及格成绩"""
    url = settings.ALL_SCORE_URL
    HEADERS['Referer'] = 'http://202.207.177.39:8089/gradeLnAllAction.do?type=ln&oper=qb'
    jar = requests.cookies.RequestsCookieJar()
    jar.set(cookies['name'], cookies['value'], domain=cookies['domain'], path=cookies['path'])
    response = requests.get(url, headers=HEADERS, cookies=jar)
    html = etree.HTML(response.text)
    tables = html.xpath('//table[@class="displayTag"]|//table[@class="displayTag"]/following-sibling::*[1]')
    processor = Processor(username)
    processor.process_jg_elements(tables)


@app.task
@retry(tries=3)
def get_bjg_score(username, cookies):
    """查询不及格成绩"""
    bjg_url = settings.FAIL_SCORE_URL
    jar = requests.cookies.RequestsCookieJar()
    jar.set(cookies['name'], cookies['value'], domain=cookies['domain'], path=cookies['path'])
    HEADERS['Referer'] = 'http://202.207.177.39:8089/gradeLnAllAction.do?type=ln&oper=qb'
    response = requests.get(bjg_url, headers=HEADERS, cookies=jar)
    html = etree.HTML(response.text)
    sbjg, cbjg = html.xpath('//table[@class="displayTag"]')
    processor = Processor(username)
    processor.process_bjg_elements(sbjg, 'sbjg')
    processor.process_bjg_elements(cbjg, 'cbjg')


@app.task
@retry(tries=3)
def get_sx_score(username, cookies):
    """课程属性成绩"""
    url = settings.COURSE_ATTRIBUTES_URL
    jar = requests.cookies.RequestsCookieJar()
    jar.set(cookies['name'], cookies['value'], domain=cookies['domain'], path=cookies['path'])
    HEADERS['Referer'] = 'http://202.207.177.39:8089/gradeLnAllAction.do?type=ln&oper=sx'
    response = requests.get(url, headers=HEADERS, cookies=jar)
    html = etree.HTML(response.text)
    sx_bx, sx_xx, sx_rx = html.xpath('//table[@class="displayTag"]')
    processor = Processor(username)
    processor.process_sx_elements(sx_bx, 'sx_bx')
    processor.process_sx_elements(sx_xx, 'sx_xx')
    processor.process_sx_elements(sx_rx, 'sx_rx')
