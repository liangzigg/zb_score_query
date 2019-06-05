from django.conf import settings
from lxml import etree
from pymongo import MongoClient


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
        """处理属性信息"""
        try:
            db = self.client.sx
            tr_list = self.process_tr(element, mode)
            if tr_list:
                db[self.collection].insert_many(tr_list)
        except Exception:
            return


def process_info(response):
    """处理个人学籍信息"""
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
