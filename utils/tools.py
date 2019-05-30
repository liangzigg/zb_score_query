import copy
import time

from django.conf import settings
from lxml import etree
import requests
from PIL import Image
from pymongo import MongoClient
from pytesseract import pytesseract
from selenium import webdriver

from pyvirtualdisplay import Display
from retry import retry


@retry(tries=2)
def get_news():
    url = settings.NEWS_URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        'Referer': 'http://www.nuc.edu.cn'
    }
    response = requests.get(url, headers=headers, timeout=3)
    text = response.content.decode('utf-8')
    html = etree.HTML(text)
    news = html.xpath('//div[@class="list_con_rightlist"]/ul/li')
    result = list()
    for li in news:
        new = dict()
        new['url'] = li.xpath('a/@href')[0].replace('..', 'http://www.nuc.edu.cn').replace('#tips', '')
        new['title'] = li.xpath('a/text()')[0]
        new['date'] = li.xpath('span/text()')[0][5:]
        result.append(new)
    return result


@retry(tries=3)
def get_cookies(username, password):
    """获取个人门户cookie"""
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('window-size=1920x1080')  # 指定浏览器分辨率
        options.add_argument(
            'user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"')
        driver = webdriver.Chrome(
            executable_path='/media/wxl/a84d5450-ee22-469c-a813-c774821af033/wangxl/chromedriver/chromedriver',
            options=options)
        # 访问个人门户登录页
        print('----------正在访问登录页面----------')
        driver.delete_all_cookies()
        driver.get(settings.LOGIN_URL)
        # 获取验证码图片
        print('----------正在获取验证码----------')
        imgelement = driver.find_element_by_xpath('//*[@id="captchaimg"]')
        locations = imgelement.location
        sizes = imgelement.size
        rangle = (int(locations['x']), int(locations['y']), int(
            locations['x'] + sizes['width']), int(locations['y'] + sizes['height']))
        path1 = '/home/wxl/Desktop/test' + str(2)
        path2 = '/home/wxl/Desktop/test' + str(3)
        driver.get_screenshot_as_file(str(path1) + '.png')

        img = Image.open(str(path1) + ".png")
        jpg = img.crop(rangle)
        jpg.save(str(path2) + ".png")
        image = Image.open(str(path2) + ".png")
        image.load()
        # 识别验证码图片
        print('----------正在识别验证码----------')
        code = pytesseract.image_to_string(image)
        image = Image.open(str(path2) + ".png")
        image.load()
        codes = pytesseract.image_to_string(image)
        # 填写登录信息，并登录
        print('----------正在登录----------')
        driver.find_element_by_xpath('//*[@id="username"]').clear()
        driver.find_element_by_xpath('//*[@id="username"]').send_keys(username)
        driver.find_element_by_xpath('//*[@id="password"]').clear()
        driver.find_element_by_xpath('//*[@id="password"]').send_keys(password)
        driver.find_element_by_xpath('//*[@id="j_captcha_response"]').clear()
        driver.find_element_by_xpath('//*[@id="j_captcha_response"]').send_keys(codes)
        driver.find_element_by_xpath(
            '//*[@id="thetable"]/div[7]/span[1]/input[3]').click()
        time.sleep(2)
        # driver.maximize_window()
        driver.find_element_by_id('134871694799031620').click()
        print('----------登录成功-----------')
        time.sleep(2)
        print('--------获取cookies---------')
        driver.switch_to.window(driver.window_handles[1])
        cookies = driver.get_cookies()  # 获取cookie
        print('--------退出浏览器-----------')
        driver.quit()  # 退出浏览器

        display.stop()
        return cookies[0]
    except Exception as e:
        print(e)
        return None


def get_info(url, cookies):
    """获取学生信息"""
    try:
        jar = requests.cookies.RequestsCookieJar()
        jar.set(cookies['name'], cookies['value'], domain=cookies['domain'], path=cookies['path'])
        print('访问成绩数据')
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': '202.207.177.39:8089',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'http://202.207.177.39:8089/menu/menu.jsp',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
        }
        info = requests.get(url, headers=headers, cookies=jar)
        return info.content.decode('gbk')
    except Exception:
        return None


def process_info(response):
    """处理信息"""
    try:
        html = etree.HTML(response)
        td = html.xpath('//td[@class="fieldName"]')
        base_info = dict()
        school_info = dict()
        graduation_info = dict()
        for t in td[0: 23]:
            field_name = t.xpath('text()')[0].strip().replace(':', '')
            field_text = t.xpath('following-sibling::*[1]/text()')[0].strip()
            base_info.update({field_name: field_text})
        for s in td[23: 44]:
            field_name = s.xpath('text()')[0].strip().replace(':', '')
            field_text = s.xpath('following-sibling::*[1]/text()')[0].strip()
            school_info.update({field_name: field_text})
        for g in td[44:]:
            field_name = g.xpath('text()')[0].strip().replace(':', '')
            field_text = g.xpath('following-sibling::*[1]/text()')[0].strip()
            graduation_info.update({field_name: field_text})
        return base_info, school_info, graduation_info
    except Exception:
        return None


class Processor(object):
    """处理成绩信息"""

    def __init__(self, username):
        self.client = MongoClient(host=settings.MG_HOST, port=settings.MG_PORT)
        self.collection = 'u' + username

    def process_tr(self, elements, mode):
        tr_list = list()
        tr = elements.xpath('tr')
        try:
            for td in tr:
                tr_dic = dict()
                text = td.xpath('td/text() | td/p/text()')
                tr_dic['类型'] = mode
                tr_dic['课程号'] = text[0].strip()
                tr_dic['课序号'] = text[1].strip()
                tr_dic['课程名'] = text[2].strip()
                tr_dic['英文课程名'] = text[3].strip()
                tr_dic['学分'] = text[4].strip()
                tr_dic['课程属性'] = text[5].strip()
                tr_dic['成绩'] = text[7].strip()
                if 'bjg' in mode:
                    tr_dic['考试时间'] = text[9].strip()
                tr_dic['未通过原因'] = text[-1].strip()
                tr_list.append(tr_dic)
            return tr_list
        except IndexError:
            return None

    def process_jg_elements(self, elements):
        """处理全部及格成绩"""
        try:
            db = self.client.jg
            for index, table in list(enumerate(elements[::2])):
                tr_list = list()
                tr = table.xpath('tr')
                for td in tr:
                    tr_dic = dict()
                    text = td.xpath('td/text() | td/p/text()')
                    tr_dic['学期'] = '学期_' + str(index)
                    tr_dic['课程号'] = text[0].strip()
                    tr_dic['课序号'] = text[1].strip()
                    tr_dic['课程名'] = text[2].strip()
                    tr_dic['英文课程名'] = text[3].strip()
                    tr_dic['学分'] = text[4].strip()
                    tr_dic['课程属性'] = text[5].strip()
                    tr_dic['成绩'] = text[7].strip()
                    tr_list.append(tr_dic)
                db[self.collection].insert_many(tr_list)
            for i, t in list(enumerate(elements[1::2])):
                insert_data = t.xpath('tr/td/text()')[0].strip()
                db[self.collection].insert_one({'学期统计': '学期' + str(i), '数据': insert_data})
        except Exception:
            return

    def process_bjg_elements(self, elements, mode):
        """处理不及格信息"""
        try:
            db = self.client.bjg
            tr_list = self.process_tr(elements, mode)
            if tr_list:
                db[self.collection].insert_many(tr_list)
        except Exception:
            return

    def process_sx_elements(self, element, mode):
        try:
            db = self.client.sx
            tr_list = self.process_tr(element, mode)
            if tr_list:
                db[self.collection].insert_many(tr_list)
        except Exception:
            return


class Calculator(object):
    """计算绩点"""
    systems = {
        'bz': {
            '90-100': 4.0,
            '80-89': 3.0,
            '70-79': 2.0,
            '60-69': 1.0,
            '0-59': 0,
        }, 'gj': {
            '85-100': 4.0,
            '75-84': 3.0,
            '60-74': 2.0,
            '0-59': 0,
        }, 'gj2': {
            '85-100': 4.0,
            '75-84': 3.0,
            '60-74': 2.0,
            '0-59': 0,
        }, 'bd': {
            '90-100': 4.0,
            '85-89': 3.7,
            '82-84': 3.3,
            '78-81': 3.0,
            '75-77': 2.7,
            '72-74': 2.3,
            '68-71': 2.0,
            '64-67': 1.5,
            '60-63': 1.0,
            '0-59': 0
        }, 'jnd': {
            '90-100': 4.3,
            '85-89': 4.0,
            '80-84': 3.7,
            '75-79': 3.3,
            '70-74': 3.0,
            '65-69': 2.7,
            '60-64': 2.3,
            '0-59': 0
        }, 'zkd': {
            '95-100': 4.3,
            '90-94': 4.0,
            '85-89': 3.7,
            '82-84': 3.3,
            '78-81': 3.0,
            '75-77': 2.7,
            '72-74': 2.3,
            '68-71': 2.0,
            '65-67': 1.7,
            '64-64': 1.5,
            '61-63': 1.3,
            '60-60': 1.0,
            '0-59': 0
        }, 'shjd': {
            '95-100': 4.3,
            '90-94': 4.0,
            '85-89': 3.7,
            '84-80': 3.3,
            '75-79': 3.0,
            '70-74': 2.7,
            '67-79': 2.3,
            '65-66': 2.0,
            '62-64': 1.7,
            '60-61': 1.0,
            '0-59': 0
        }
    }
    format_s = {
        '优秀': 95,
        '良好': 85,
        '中': 75,
        '及格': 60,
        '不及格': 0
    }

    def __init__(self, score_list=None):
        if score_list is None:
            score_list = []
        self.score_list = score_list

    def _format_score_list(self, score_list):
        """将非数字成绩转化为数字成绩"""
        result_list = list()
        score_list = copy.deepcopy(score_list)
        for score in score_list:
            result = dict()
            try:
                result['score'] = float(score['成绩'])
            except ValueError:
                result['score'] = self.format_s[score['成绩']]
            result['credit'] = float(score['学分'])
            result_list.append(result)
        return result_list

    def _score2point(self, score_list, school):
        """将成绩转化为绩点"""
        items = copy.deepcopy(score_list)
        system = self.systems[school]
        for item in items:
            for q, p in system.items():
                low, high = q.split('-')
                if float(low) <= item['score'] <= float(high):
                    item['score'] = p
                    break
        return items

    def _calculate(self, items):
        """计算平均绩点"""
        count = 0
        credit_count = 0
        for item in items:
            credit_count += item['credit']
            count += item['score'] * item['credit']
        return format(count / credit_count, '.2f')

    def average(self, score=None, school=None):
        """平均绩点"""
        if school is None:
            school = 'bz'
        score_list = score or self.score_list
        result = self._format_score_list(score_list)
        items = self._score2point(result, school)
        return self._calculate(items)


def get_qb_score(key, client):
    """获取全部成绩"""
    jg_score = list(client.jg[key].find({'学期': {'$regex': '学期.*'}}))  # 查询及格成绩
    bjg_score = list(client.bjg[key].find({'类型': 'sbjg'}))  # 查询尚不及格成绩
    if not jg_score:
        return {'error_message': '暂无数据可进行分析,请先查询成绩!'}
    jg_score.extend(bjg_score)  # 合并成绩
    return jg_score


def get_point(key, client, school=None):
    """获取绩点"""
    scores = get_qb_score(key, client)
    if isinstance(scores, dict):
        return scores
    cal = Calculator(scores)
    current_point = cal.average(school=school)
    return current_point


if __name__ == '__main__':
    r = get_news()
    print(r)
