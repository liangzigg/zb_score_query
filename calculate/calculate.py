import copy

from PIL import Image
from pytesseract import pytesseract


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
            '70-84': 3.0,
            '60-69': 2.0,
            '0-59': 0
        }, 'gj2': {
            '85-100': 4.0,
            '75-84': 3.0,
            '60-74': 2.0,
            '0-59': 0
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
        '优秀': 90,
        '良好': 80,
        '中': 70,
        '及格': 60,
        '不及格': 0
    }
    format_zb = {
        '优秀': 4.5,
        '良好': 3.5,
        '中': 2.5,
        '及格': 1.5,
        '不及格': 0
    }

    def __init__(self, score_list=None):
        if score_list is None:
            score_list = []
        self.score_list = score_list

    def _zb_format(self, score_list):
        """中北大学计算标准"""
        score_list = copy.deepcopy(score_list)
        results = list()
        for score in score_list:
            result = dict()
            try:
                s = float(score['成绩'])
                result['score'] = s / 10 - 5
            except ValueError:
                result['score'] = self.format_zb[score['成绩']]
            result['credit'] = float(score['学分'])
            results.append(result)
        return results

    def _format_score_list(self, score_list, mode=False):
        """将非数字成绩转化为数字成绩"""
        result_list = list()
        score_list = copy.deepcopy(score_list)
        format_score = self.format_zb if mode else self.format_s
        for score in score_list:
            result = dict()
            try:
                if mode:
                    s = float(score['成绩'])
                    ss = s / 10 - 5
                    result['score'] = ss if ss > 0 else 0
                else:
                    result['score'] = float(score['成绩'])
            except ValueError:
                result['score'] = format_score[score['成绩']]
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

    @staticmethod
    def _calculate(items):
        """计算平均绩点"""
        count = 0
        credit_count = 0
        for item in items:
            credit_count += item['credit']
            count += item['score'] * item['credit']
        return format(count / credit_count, '.2f')

    def average(self, score=None, school=None):
        """平均绩点"""
        score_list = score or self.score_list
        if school is None:
            school = 'bz'
        mode = True if school == 'zb' else False
        result = self._format_score_list(score_list, mode)
        if school != 'zb':
            items = self._score2point(result, school)
            return self._calculate(items)
        return self._calculate(result)


def cracking_captcha(driver, username):
    imgelement = driver.find_element_by_xpath('//*[@id="captchaimg"]')
    locations = imgelement.location
    sizes = imgelement.size
    # 获取验证码的位置及大小
    rangle = (int(locations['x']), int(locations['y']), int(
        locations['x'] + sizes['width']), int(locations['y'] + sizes['height']))
    path1 = '/home/wxl/Desktop/all' + username
    driver.get_screenshot_as_file(path1 + '.png')
    img = Image.open(path1 + ".png")
    jpg = img.crop(rangle)  # 剪切验证码
    image = Image.open(jpg)
    image.load()  # 加载验证码
    code = pytesseract.image_to_string(image)  # 识别验证码
    return code
