from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import AnalysisResult

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    # 一覧画面に表示する項目
    list_display = ('id', 'thumbnail', 'prediction_label', 'prediction_score', 'created_at')
    # リンクにする項目
    list_display_links = ('id', 'thumbnail', 'prediction_label')
    # フィルタリング機能
    list_filter = ('created_at', 'prediction_label')
    # 検索機能
    search_fields = ('prediction_label',)

    # 管理画面で画像のサムネイルを表示するための関数
    def thumbnail(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="width: 50px; height: auto;">')
        return "画像なし"
    
    thumbnail.short_description = 'プレビュー'

