from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os


class AnalysisResult(models.Model):
    """
    画像解析結果を保存するモデル
    """
    # 画像を保存するフィールド (media/uploads フォルダに保存される)
    image = models.ImageField(
        upload_to='uploads/%Y/%m/%d/', 
        verbose_name="解析画像",
        help_text="解析対象の画像ファイル"
    )
    
    # 元のファイル名を保存（後で参照しやすくするため）
    original_filename = models.CharField(
        max_length=255, 
        verbose_name="元のファイル名",
        blank=True,
        null=True
    )
    
    # 解析結果のラベル（例: Golden Retriever）
    prediction_label = models.CharField(
        max_length=255, 
        verbose_name="予測ラベル",
        db_index=True  # 検索を高速化
    )
    
    # 解析結果の確率（例: 95.50）
    prediction_score = models.FloatField(
        verbose_name="確信度(%)",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="予測の確信度（0-100%）"
    )
    
    # 解析日時
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="解析日時",
        db_index=True  # 日付での並び替えを高速化
    )
    
    # 更新日時（将来的に再解析機能を追加する場合に備えて）
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="更新日時"
    )
    
    # 解析に使用したモデル情報（将来的に複数のモデルを使う場合に備えて）
    model_version = models.CharField(
        max_length=50,
        verbose_name="モデルバージョン",
        default="v1.0",
        blank=True
    )
    
    # 処理時間（パフォーマンス測定用）
    processing_time = models.FloatField(
        verbose_name="処理時間(秒)",
        null=True,
        blank=True,
        help_text="画像解析にかかった時間"
    )

    class Meta:
        verbose_name = "解析結果"
        verbose_name_plural = "解析結果一覧"
        ordering = ['-created_at']  # デフォルトで新しい順に並べる
        indexes = [
            models.Index(fields=['-created_at', 'prediction_label']),
        ]

    def __str__(self):
        return f"{self.prediction_label} ({self.prediction_score:.2f}%) - {self.created_at.strftime('%Y/%m/%d %H:%M')}"

    def get_image_filename(self):
        """画像のファイル名を取得"""
        if self.image:
            return os.path.basename(self.image.name)
        return None
    
    def get_confidence_level(self):
        """確信度のレベルを文字列で返す"""
        if self.prediction_score >= 90:
            return "非常に高い"
        elif self.prediction_score >= 70:
            return "高い"
        elif self.prediction_score >= 50:
            return "中程度"
        else:
            return "低い"
    
    def is_recent(self, hours=24):
        """指定時間以内の解析結果かどうかを判定"""
        time_diff = timezone.now() - self.created_at
        return time_diff.total_seconds() < hours * 3600
    
    @property
    def formatted_score(self):
        """確信度を整形して返す（小数点2桁）"""
        return f"{self.prediction_score:.2f}%"
    
    def delete(self, *args, **kwargs):
        """削除時に画像ファイルも削除"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

