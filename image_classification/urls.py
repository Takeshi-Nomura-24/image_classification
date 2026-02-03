"""
image_classification URL Configuration

メインのURLルーティング設定
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # ==================================================
    # 管理画面
    # ==================================================
    path('admin/', admin.site.urls),
    
    # ==================================================
    # アプリケーションのURL
    # ==================================================
    path('', include('predict.urls')),
    
    # ==================================================
    # その他のURL（将来的な拡張用）
    # ==================================================
    # path('api/', include('api.urls')),  # REST API用
    # path('accounts/', include('django.contrib.auth.urls')),  # 認証用
]

# ==================================================
# メディアファイルの配信（開発環境のみ）
# ==================================================
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, 
        document_root=settings.STATIC_ROOT
    )

# ==================================================
# カスタムエラーハンドラー
# ==================================================
# 本番環境用のカスタムエラーページ
# handler404 = 'predict.views.custom_404'
# handler500 = 'predict.views.custom_500'
# handler403 = 'predict.views.custom_403'
# handler400 = 'predict.views.custom_400'

# ==================================================
# 管理画面のカスタマイズ
# ==================================================
admin.site.site_header = 'AI Image Classifier 管理画面'
admin.site.site_title = 'AI Image Classifier'
admin.site.index_title = 'ダッシュボード'
