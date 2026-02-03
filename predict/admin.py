"""
predict app Admin Configuration

Django管理画面のカスタマイズ
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import AnalysisResult


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    """
    解析結果モデルの管理画面カスタマイズ
    """
    
    # ==================================================
    # リスト表示設定
    # ==================================================
    
    list_display = [
        'id',
        'thumbnail_preview',
        'prediction_label',
        'colored_score',
        'confidence_level_display',
        'created_at',
        'processing_time_display',
    ]
    
    list_display_links = ['id', 'thumbnail_preview', 'prediction_label']
    
    list_filter = [
        'created_at',
        'model_version',
        ('prediction_score', admin.EmptyFieldListFilter),
    ]
    
    search_fields = [
        'prediction_label',
        'original_filename',
    ]
    
    date_hierarchy = 'created_at'
    
    list_per_page = 25
    
    ordering = ['-created_at']
    
    # ==================================================
    # 詳細表示設定
    # ==================================================
    
    fieldsets = (
        ('画像情報', {
            'fields': ('image', 'original_filename', 'image_preview')
        }),
        ('解析結果', {
            'fields': (
                'prediction_label',
                'prediction_score',
                'model_version',
            )
        }),
        ('処理情報', {
            'fields': (
                'processing_time',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    readonly_fields = [
        'image_preview',
        'created_at',
        'updated_at',
    ]
    
    # ==================================================
    # アクション
    # ==================================================
    
    actions = [
        'delete_selected_with_images',
        'export_as_csv',
    ]
    
    # ==================================================
    # カスタムメソッド
    # ==================================================
    
    def thumbnail_preview(self, obj):
        """サムネイル画像の表示"""
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="60" '
                'style="object-fit: cover; border-radius: 8px;" />',
                obj.image.url
            )
        return '-'
    thumbnail_preview.short_description = 'サムネイル'
    
    def image_preview(self, obj):
        """詳細画面での画像プレビュー"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 500px; border-radius: 12px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = '画像プレビュー'
    
    def colored_score(self, obj):
        """確信度を色付きで表示"""
        if obj.prediction_score >= 70:
            color = '#48bb78'  # 緑
        elif obj.prediction_score >= 50:
            color = '#ed8936'  # オレンジ
        else:
            color = '#e53e3e'  # 赤
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}%</span>',
            color,
            obj.prediction_score
        )
    colored_score.short_description = '確信度'
    colored_score.admin_order_field = 'prediction_score'
    
    def confidence_level_display(self, obj):
        """確信度レベルをバッジで表示"""
        level = obj.get_confidence_level()
        
        color_map = {
            '非常に高い': '#48bb78',
            '高い': '#4299e1',
            '中程度': '#ed8936',
            '低い': '#e53e3e',
        }
        
        color = color_map.get(level, '#718096')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 0.85em; font-weight: bold;">{}</span>',
            color,
            level
        )
    confidence_level_display.short_description = '信頼度'
    
    def processing_time_display(self, obj):
        """処理時間の表示"""
        if obj.processing_time:
            return f'{obj.processing_time:.2f}秒'
        return '-'
    processing_time_display.short_description = '処理時間'
    processing_time_display.admin_order_field = 'processing_time'
    
    # ==================================================
    # カスタムアクション
    # ==================================================
    
    def delete_selected_with_images(self, request, queryset):
        """選択された項目を画像ファイルごと削除"""
        count = queryset.count()
        for obj in queryset:
            obj.delete()  # モデルのdelete()が画像も削除
        
        self.message_user(
            request,
            f'{count}件の解析結果と画像ファイルを削除しました。'
        )
    delete_selected_with_images.short_description = '選択した項目を画像ごと削除'
    
    def export_as_csv(self, request, queryset):
        """選択された項目をCSVでエクスポート"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analysis_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # BOM for Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'ID',
            '予測ラベル',
            '確信度(%)',
            '元のファイル名',
            'モデルバージョン',
            '処理時間(秒)',
            '解析日時',
        ])
        
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.prediction_label,
                obj.prediction_score,
                obj.original_filename or '',
                obj.model_version,
                obj.processing_time or '',
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            ])
        
        return response
    export_as_csv.short_description = '選択した項目をCSVでエクスポート'
    
    # ==================================================
    # 統計情報の表示
    # ==================================================
    
    def changelist_view(self, request, extra_context=None):
        """一覧画面に統計情報を追加"""
        extra_context = extra_context or {}
        
        # 統計情報を計算
        stats = AnalysisResult.objects.aggregate(
            total_count=Count('id'),
            avg_confidence=Avg('prediction_score'),
            avg_processing_time=Avg('processing_time'),
        )
        
        extra_context['stats'] = {
            'total_count': stats['total_count'] or 0,
            'avg_confidence': round(stats['avg_confidence'] or 0, 2),
            'avg_processing_time': round(stats['avg_processing_time'] or 0, 2),
        }
        
        return super().changelist_view(request, extra_context=extra_context)


# ==================================================
# 管理画面の表示をカスタマイズ（オプション）
# ==================================================

# 管理画面のタイトルなどは project_urls.py で設定済み
