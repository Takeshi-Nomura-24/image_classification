from django.db import models

class AnalysisResult(models.Model):
    # 画像を保存するフィールド (media/uploads フォルダに保存される)
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/', verbose_name="解析画像")
    
    # 解析結果のラベル（例: Golden Retriever）
    prediction_label = models.CharField(max_length=255, verbose_name="予測ラベル")
    
    # 解析結果の確率（例: 95.50）
    prediction_score = models.FloatField(verbose_name="確信度(%)")
    
    # 解析日時
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="解析日時")

    def __str__(self):
        return f"{self.prediction_label} ({self.prediction_score}%) - {self.created_at}"

    class Meta:
        verbose_name = "解析結果"
        verbose_name_plural = "解析結果一覧"
