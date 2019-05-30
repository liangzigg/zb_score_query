from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin


class CheckStatus(MiddlewareMixin):

    def process_request(self, request):
        # 在request到达view之前执行
        login_path = ['student', ]  # 需要登录权限才能访问的URL地址
        site = request.path_info.split('/')[1]
        operate = request.path_info.split('/')[2]
        status = request.session.get('username')  # 获取session中的登录标识
        if not status and site in login_path and operate != 'login':
            return redirect('student:login')
