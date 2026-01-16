from django.apps import AppConfig
from keras.applications.vgg16 import VGG16

class PredictConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'predict'

    def ready(self):
        # サーバー起動時に一度だけモデルをロード
        self.model = VGG16(weights='imagenet')