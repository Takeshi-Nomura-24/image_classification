from django.urls import path
from . import views

app_name = 'predict'

urlpatterns = [
    path('', views.index, name='index'),
    path('history/', views.view_data, name='view_data'), # 一覧表示
    path('delete/<int:pk>/', views.delete_data, name='delete_data'), # 削除実行
]