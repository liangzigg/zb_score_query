from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic.base import View

from spider.spider import get_news


class Index(View):
    """首页"""
    def get(self, request):
        return render(request, 'index.html')


class GetNews(View):
    """获取新闻信息"""
    def get(self, request):
        news = get_news()
        return JsonResponse({'status': True, 'news': news})


def page_not_found(request,**kwargs):
    """404页面"""
    return render(request, '404.html')
