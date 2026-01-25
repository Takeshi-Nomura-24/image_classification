from django.apps import AppConfig
import onnxruntime as ort
import os
from django.conf import settings

class PredictConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'predict'

    def ready(self):
        # モデルファイルのパス（プロジェクト直下に置く場合）
        model_path = os.path.join(settings.BASE_DIR, 'mobilenet_v2.onnx')
        
        # モデルが存在する場合のみロード（ビルド時のエラー回避）
        if os.path.exists(model_path):
            # 推論セッションの作成（CPU指定）
            self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
            # 入力名の取得（推論時に必要）
            self.input_name = self.session.get_inputs()[0].name
        else:
            self.session = None
