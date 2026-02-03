import logging
import os
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class PredictConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'predict'
    verbose_name = '画像解析アプリケーション'
    
    # モデルインスタンスを保持するクラス変数
    model = None
    model_name = 'EfficientNetB0'
    model_version = 'v1.0'

    def ready(self):
        """
        アプリケーション起動時に一度だけ実行される初期化処理
        """
        # Django起動時の重複読み込みを防ぐ
        if os.environ.get('RUN_MAIN') != 'true':
            return
        
        try:
            self._load_ai_model()
            self._register_signals()
            logger.info(f"{self.verbose_name} の初期化が完了しました")
        except Exception as e:
            logger.error(f"アプリケーション初期化エラー: {e}")
            raise

    def _load_ai_model(self):
        """
        AIモデルをメモリにロードする（EfficientNetB0使用）
        """
        try:
            from keras.applications.efficientnet import EfficientNetB0
            
            logger.info(f"{self.model_name} モデルをロード中...")
            
            # EfficientNetB0のロード（軽量で高精度）
            self.__class__.model = EfficientNetB0(weights='imagenet')
            
            logger.info(f"{self.model_name} モデルのロードが完了しました")
            logger.info(f"モデルバージョン: {self.model_version}")
            
            # モデル情報のログ出力（デバッグ用）
            if settings.DEBUG:
                self._log_model_info()
        
        except ImportError as e:
            logger.error(f"Kerasのインポートエラー: {e}")
            logger.error("pip install tensorflow keras を実行してください")
            raise
        
        except Exception as e:
            logger.error(f"モデルロードエラー: {e}")
            raise

    def _log_model_info(self):
        """
        モデルの詳細情報をログに出力（デバッグモード時のみ）
        """
        if self.__class__.model:
            try:
                total_params = self.__class__.model.count_params()
                logger.debug(f"モデルパラメータ数: {total_params:,}")
                logger.debug(f"入力サイズ: {self.__class__.model.input_shape}")
                logger.debug(f"出力サイズ: {self.__class__.model.output_shape}")
            except Exception as e:
                logger.warning(f"モデル情報の取得に失敗: {e}")

    def _register_signals(self):
        """
        シグナルハンドラーの登録（将来的な機能拡張用）
        """
        pass

    @classmethod
    def get_model(cls):
        """
        ロード済みのモデルインスタンスを取得する
        
        Returns:
            ロード済みのKerasモデル
            
        Raises:
            RuntimeError: モデルが未ロードの場合
        """
        if cls.model is None:
            error_msg = "モデルがロードされていません。アプリケーションの初期化を確認してください。"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return cls.model

    @classmethod
    def get_model_info(cls):
        """
        モデル情報を辞書形式で取得する
        
        Returns:
            モデル情報の辞書
        """
        return {
            'name': cls.model_name,
            'version': cls.model_version,
            'is_loaded': cls.model is not None,
            'input_shape': cls.model.input_shape if cls.model else None,
            'output_shape': cls.model.output_shape if cls.model else None,
        }

