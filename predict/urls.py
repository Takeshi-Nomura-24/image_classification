"""
predict app URL Configuration

画像解析アプリケーションのURLルーティング設定
"""

from django.urls import path
from . import views

app_name = 'predict'

urlpatterns = [
    # ==================================================
    # メイン機能
    # ==================================================
    
    # トップページ（画像アップロード・解析）
    path(
        '', 
        views.index, 
        name='index'
    ),
    
    # 解析履歴一覧
    path(
        'history/', 
        views.view_data, 
        name='view_data'
    ),
    
    # ==================================================
    # データ操作
    # ==================================================
    
    # 解析結果の削除
    path(
        'delete/<int:pk>/', 
        views.delete_data, 
        name='delete_data'
    ),
    
    # ==================================================
    # API・統計（将来的な拡張用）
    # ==================================================
    
    # 統計情報取得API（オプション）
    # path(
    #     'api/statistics/', 
    #     views.get_statistics, 
    #     name='statistics'
    # ),
    
    # 特定の解析結果の詳細表示（オプション）
    # path(
    #     'result/<int:pk>/', 
    #     views.result_detail, 
    #     name='result_detail'
    # ),
    
    # 解析結果のエクスポート（CSV/JSON）（オプション）
    # path(
    #     'export/<str:format>/', 
    #     views.export_data, 
    #     name='export_data'
    # ),
    
    # バッチ削除（オプション）
    # path(
    #     'delete/batch/', 
    #     views.batch_delete, 
    #     name='batch_delete'
    # ),
]
