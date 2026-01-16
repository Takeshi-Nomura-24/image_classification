import os
from django.apps import AppConfig

class ImageClassificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'image_classification'
    
    # モデルを保持する変数（クラス変数）
    image_model = None

    def ready(self):
        # 1. 開発用サーバーの二重起動防止 (リローダー側は無視)
        # ※本番環境（Gunicorn等）ではこの環境変数が無い場合があるため、
        # DEBUG=Trueの時のみチェックする形でも良いですが、このままでも概ね問題ありません。
        if os.environ.get('RUN_MAIN') != 'true':
            return

        # 2. ロード処理
        try:
            # 実行時インポートにより、アプリ起動をスムーズにする
            from keras.applications.vgg16 import VGG16
            
            if ImageClassificationConfig.image_model is None:
                print("--- AIモデル(VGG16)をロード中... ---")
                # クラス変数にロード（シングルトン的な扱い）
                ImageClassificationConfig.image_model = VGG16(weights='imagenet')
                print("--- モデルのロードが完了しました！ ---")
                
        except ImportError:
            print("エラー: TensorFlow/Kerasがインストールされていないか、インポートパスが間違っています。")
        except Exception as e:
            print(f"ロード中に予期せぬエラーが発生しました: {e}")
