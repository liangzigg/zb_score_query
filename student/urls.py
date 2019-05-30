from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('personal/', views.Personal.as_view(), name='personal'),
    path('personal/info', views.StudentInfo.as_view(), name='info'),
    path('personal/score', views.ScoreInfo.as_view(), name='score'),
    path('personal/gpa', views.GPA.as_view(), name='gpa'),
    path('personal/charts', views.Charts.as_view(), name='charts'),
    path('personal/exportExcel', views.ExportExcel.as_view(), name='export_excel'),
]
