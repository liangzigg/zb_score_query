import json
from io import BytesIO

import xlwt
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, reverse, redirect
from django.views.generic.base import View
from pymongo import MongoClient

from celery_tasks.tasks import get_jg_score, get_bjg_score, get_sx_score
from utils.charts import json_response, charts
from utils.tools import get_point
from spider.spider import get_cookies, get_info
from process.process import process_info

from .models import User


class Login(View):
    """学生登录"""
    client = MongoClient(settings.MG_HOST, settings.MG_PORT)

    def get(self, request):
        return render(request, 'student/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
            request.session['username'] = user.username
            return JsonResponse({'status': True, 'url': reverse('student:personal')})
        except User.DoesNotExist:
            cookies = get_cookies(username, password)
            if not cookies:
                return JsonResponse({'status': False, 'msg': '登录失败!'})
        key = 'u' + username
        user = User.objects.create(username=username, password=password, mg_key=key)
        jg = list(self.client.jg[user.mg_key].find({"学期": {"$regex": '学期.*'}}))
        bjg = list(self.client.bjg[user.mg_key].find({"类型": {"$regex": ".*bjg"}}))
        sx = list(self.client.sx[user.mg_key].find({"类型": {"$regex": "sx.*"}}))
        if not jg:
            get_jg_score.delay(user.username, cookies)
        if not bjg:
            get_bjg_score.delay(user.username, cookies)
        if not sx:
            get_sx_score.delay(user.username, cookies)
        request.session['cookies'] = cookies
        request.session['username'] = user.username
        return JsonResponse({'status': True, 'url': reverse('student:personal')})


class Logout(View):
    """退出"""

    def get(self, request):
        if not request.session.get('username'):
            return redirect('student:login')
        request.session.flush()
        return redirect('analysis:index')


class Personal(View):
    """欢迎界面"""

    def get(self, request):
        return render(request, 'student/welcome.html')


class StudentInfo(View):
    """个人信息"""

    def get(self, request):
        context = {
            'base_info': dict(),
            'school_info': dict(),
            'graduation_info': dict()
        }
        info_url = settings.INFO_URL
        cookies = request.session.get('cookies')
        info_text = get_info(info_url, cookies)
        if not info_text:
            return render(request, 'student/info.html', context=context)
        results = process_info(info_text)
        if not results:
            return render(request, 'student/info.html', context=context)
        context = {
            'base_info': results[0],
            'school_info': results[1],
            'graduation_info': results[2]
        }
        return render(request, 'student/info.html', context=context)


class ScoreInfo(View):
    """获取学生成绩"""
    client = MongoClient(settings.MG_HOST, settings.MG_PORT)

    def get(self, request):
        info_type = request.GET.get('oper')
        if info_type == 'bjg':
            db = self.client.bjg
            collection = 'u' + request.session.get('username')
            cbjg_list = db[collection].find({'类型': 'cbjg'})
            sbjg_list = db[collection].find({'类型': 'sbjg'})
            return render(request, 'student/bjg_tables.html', {'cbjg_list': list(cbjg_list),
                                                               'sbjg_list': list(sbjg_list)})
        if info_type == 'sx':
            db = self.client.sx
            collection = 'u' + request.session.get('username')
            bx_list = db[collection].find({'类型': 'sx_bx'})
            xx_list = db[collection].find({'类型': 'sx_xx'})
            rx_list = db[collection].find({'类型': 'sx_rx'})
            return render(request, 'student/sx_tables.html', {'bx_list': list(bx_list),
                                                              'xx_list': list(xx_list),
                                                              'rx_list': list(rx_list)})
        if info_type == 'qb':
            db = self.client.jg
            collection = 'u' + request.session.get('username')
            terms = db[collection].aggregate([{'$group': {'_id': '$学期'}}])
            term_list = list()
            total_list = list()
            for i in range(0, len(list(terms)) - 1):
                result = db[collection].find({'学期': '学期_' + str(i)})
                total = db[collection].find({'学期统计': '学期' + str(i)})
                term_list.append(list(result))
                total_list.append(list(total)[0])
            return render(request, 'student/qb_tables.html', {'term_list': term_list,
                                                              'total_list': total_list})


class GPA(View):
    """绩点查询"""
    client = MongoClient(settings.MG_HOST, settings.MG_PORT)

    def get(self, request):
        key = 'u' + request.session.get('username')
        school = request.GET.get('mode')
        result = get_point(key, self.client, school)
        if school is None:
            return render(
                request, 'student/gpa.html',
                {'current_point': result['error_message'] if isinstance(result, dict) else result}
            )
        return JsonResponse({'status': True, 'point': result})


class Charts(View):
    """图表分析"""

    def get(self, request):

        return render(request, 'student/charts.html')

    def post(self, request):
        key = 'u' + request.session.get('username')
        return json_response(json.loads(charts(key)))


class ExportExcel(View):
    """导出Excel表"""
    client = MongoClient(settings.MG_HOST, settings.MG_PORT)

    def get(self, request):
        # key = 'u' + '1509044144'
        key = 'u' + request.session.get('username')
        school = request.GET.get('mode')
        point = get_point(key, self.client, school)

        jg_score = list(self.client.jg[key].find({'学期': {'$regex': '学期.*'}}))  # 查询及格成绩
        bjg_score = list(self.client.bjg[key].find({'类型': 'sbjg'}))  # 查询尚不及格成绩
        if not jg_score:
            return JsonResponse({'status': False, 'msg': '暂无数据可进行导出!'})
        jg_score.extend(bjg_score)

        # 设置HTTPResponse的类型
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment;filename=report.xls'
        # 创建一个文件对象
        wb = xlwt.Workbook(encoding='utf8')
        # 创建一个sheet对象
        sheet = wb.add_sheet('report-sheet')

        # 实线边框
        borders = xlwt.Borders()
        borders.left = xlwt.Borders.THIN
        borders.right = xlwt.Borders.THIN
        borders.top = xlwt.Borders.THIN
        borders.bottom = xlwt.Borders.THIN

        # 设置文件头的样式
        hfont = xlwt.Font()
        hfont.name = '宋体'
        hfont.height = 20*14
        style = xlwt.XFStyle()
        style.font = hfont
        style.borders = borders

        # 设置成绩信息样式
        bfont = xlwt.Font()
        bfont.name = '宋体'
        bfont.height = 20*14
        bstyle = xlwt.XFStyle()
        bstyle.font = bfont
        bstyle.borders = borders

        # 设置统计信息样式
        afont = xlwt.Font()
        afont.name = '宋体'
        afont.height = 20*14
        afont.colour_index = 2
        astyle = xlwt.XFStyle()
        astyle.font = afont
        astyle.borders = borders
        # 写入文件标题
        sheet.write(0, 0, '课程名称', style)
        sheet.write(0, 1, '成绩', style)
        sheet.write(0, 2, '学分', style)

        # 写入数据
        data_row = 1
        total = 0
        for i in jg_score:
            total += float(i['学分'])
            sheet.write(data_row, 0, i['课程名'], bstyle)
            sheet.write(data_row, 1, i['成绩'], bstyle)
            sheet.write(data_row, 2, i['学分'], bstyle)
            data_row = data_row + 1
        sheet.write(data_row, 0, '已获得总学分数(Total Credit)', astyle)
        sheet.write(data_row, 1, total, astyle)
        sheet.write(data_row + 1, 0, '平均学分绩点(General Point Average)', astyle)
        sheet.write(data_row + 1, 1, point, astyle)
        # 设置单元格宽度
        sheet.col(0).width = 18000
        sheet.col(1).width = 4000
        sheet.col(2).width = 4000

        # 写出到IO
        output = BytesIO()
        wb.save(output)
        # 重新定位到开始
        output.seek(0)
        response.write(output.getvalue())
        return response
