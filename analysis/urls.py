from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('get_news/', views.GetNews.as_view(), name='get_news')
]
