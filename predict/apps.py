# apps.py
from django.apps import AppConfig
# VGG16 を MobileNetV2 に変更
from keras.applications.mobilenet_v2 import MobileNetV2

class PredictConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'predict'

    def ready(self):
        # MobileNetV2 をロード (VGG16より圧倒的に軽いです)
        self.model = MobileNetV2(weights='imagenet')
