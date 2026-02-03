import io
import json
import os
import time
import logging
from typing import Optional, List, Dict, Any

import numpy as np
import cv2
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
# EfficientNetB0用のインポートに変更
from keras.applications.efficientnet import preprocess_input, decode_predictions

from .models import AnalysisResult

# ロガーの設定
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 定数
# ------------------------------------------------------------------
IMAGE_SIZE = (224, 224)  # EfficientNetB0も224x224
TOP_PREDICTIONS = 5
ITEMS_PER_PAGE = 10
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}


# ------------------------------------------------------------------
# ヘルパー関数: ImageNet IDを日本語ラベルに変換
# ------------------------------------------------------------------
def get_japanese_label(class_id: str) -> Optional[str]:
    """
    JSONファイルからImageNet ID（n04285008等）に対応する日本語名を取得する。
    
    Args:
        class_id: ImageNetクラスID
        
    Returns:
        日本語ラベル、見つからない場合はNone
    """
    json_path = os.path.join(settings.BASE_DIR, 'imagenet_class_index_jp.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            j_labels = json.load(f)
        
        # j_labelsがリスト形式の場合、中身を走査してIDが一致するものを探す
        for item in j_labels:
            if item.get('num') == class_id:
                return item.get('ja')
        return None
    
    except FileNotFoundError:
        logger.error(f"日本語ラベルファイルが見つかりません: {json_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSONファイルの読み込みエラー: {e}")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return None


def validate_image_file(file) -> tuple[bool, Optional[str]]:
    """
    アップロードされた画像ファイルのバリデーション
    
    Args:
        file: アップロードされたファイルオブジェクト
        
    Returns:
        (バリデーション結果, エラーメッセージ)
    """
    # ファイルの存在チェック
    if not file:
        return False, "ファイルが選択されていません"
    
    # ファイルサイズチェック
    if file.size > MAX_FILE_SIZE:
        return False, f"ファイルサイズが大きすぎます（最大{MAX_FILE_SIZE // (1024*1024)}MB）"
    
    # 拡張子チェック
    ext = file.name.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"許可されていないファイル形式です（対応形式: {', '.join(ALLOWED_EXTENSIONS)}）"
    
    return True, None


def preprocess_image(file) -> Optional[np.ndarray]:
    """
    アップロードされた画像ファイルを前処理する（EfficientNetB0用）
    
    Args:
        file: アップロードされたファイルオブジェクト
        
    Returns:
        前処理済みの画像配列、失敗時はNone
    """
    try:
        # ファイルをバイト列として読み込み
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error("画像のデコードに失敗しました")
            return None
        
        # EfficientNetB0用の前処理 (224x224へリサイズ)
        img_resized = cv2.resize(img, IMAGE_SIZE)
        x = np.expand_dims(img_resized, axis=0)
        x = preprocess_input(x)
        
        return x
    
    except Exception as e:
        logger.error(f"画像の前処理エラー: {e}")
        return None


def perform_prediction(preprocessed_image: np.ndarray) -> Optional[List[tuple]]:
    """
    AI推論を実行する
    
    Args:
        preprocessed_image: 前処理済みの画像配列
        
    Returns:
        予測結果のリスト、失敗時はNone
    """
    try:
        # AppConfigでロード済みのモデルを使用
        model = apps.get_app_config('predict').model
        preds = model.predict(preprocessed_image)
        results = decode_predictions(preds, top=TOP_PREDICTIONS)[0]
        return results
    
    except Exception as e:
        logger.error(f"推論エラー: {e}")
        return None


def format_predictions(results: List[tuple]) -> List[Dict[str, Any]]:
    """
    解析結果を日本語化して整形する
    
    Args:
        results: decode_predictionsの結果
        
    Returns:
        整形された予測結果のリスト
    """
    predictions = []
    for class_id, name, prob in results:
        # 日本語ラベル取得を試みる。なければ英語名を整形。
        jp_name = get_japanese_label(class_id) or name.replace('_', ' ')
        
        predictions.append({
            'name': jp_name,
            'prob': f"{prob * 100:.2f}%",
            'raw_prob': prob * 100,
            'class_id': class_id
        })
    
    return predictions


def save_analysis_result(file, results: List[tuple], processing_time: float) -> Optional[AnalysisResult]:
    """
    解析結果をデータベースに保存する
    
    Args:
        file: アップロードされたファイルオブジェクト
        results: decode_predictionsの結果
        processing_time: 処理時間（秒）
        
    Returns:
        保存されたAnalysisResultインスタンス、失敗時はNone
    """
    try:
        top_id, top_name, top_prob = results[0]
        top_jp_name = get_japanese_label(top_id) or top_name.replace('_', ' ')
        
        # ファイルポインタを先頭に戻してから保存
        file.seek(0)
        
        result_instance = AnalysisResult(
            image=file,
            original_filename=file.name,
            prediction_label=top_jp_name,
            prediction_score=round(float(top_prob * 100), 2),
            processing_time=processing_time,
            model_version='EfficientNetB0-v1.0'  # モデルバージョンを更新
        )
        result_instance.save()
        
        logger.info(f"解析結果を保存しました: {result_instance.id}")
        return result_instance
    
    except Exception as e:
        logger.error(f"データベース保存エラー: {e}")
        return None


# ------------------------------------------------------------------
# メイン画面（解析実行）
# ------------------------------------------------------------------
@require_http_methods(["GET", "POST"])
def index(request):
    """
    画像アップロードと解析を行うメイン画面
    """
    predictions = None
    image_url = None

    if request.method == 'POST':
        file = request.FILES.get('imageFile')
        
        # 1. ファイルバリデーション
        is_valid, error_message = validate_image_file(file)
        if not is_valid:
            messages.error(request, error_message)
            return render(request, 'index.html', {
                'predictions': None,
                'image_data': None
            })
        
        # 処理時間の計測開始
        start_time = time.time()
        
        # 2. 画像の前処理
        preprocessed_image = preprocess_image(file)
        if preprocessed_image is None:
            messages.error(request, "画像の読み込みに失敗しました。別の画像をお試しください。")
            return render(request, 'index.html', {
                'predictions': None,
                'image_data': None
            })
        
        # 3. AI推論実行
        results = perform_prediction(preprocessed_image)
        if results is None:
            messages.error(request, "画像解析に失敗しました。もう一度お試しください。")
            return render(request, 'index.html', {
                'predictions': None,
                'image_data': None
            })
        
        # 処理時間の計測終了
        processing_time = time.time() - start_time
        
        # 4. 解析結果の整形
        predictions = format_predictions(results)
        
        # 5. データベースへの保存
        result_instance = save_analysis_result(file, results, processing_time)
        if result_instance:
            image_url = result_instance.image.url
            messages.success(request, f"画像解析が完了しました（処理時間: {processing_time:.2f}秒）")
        else:
            messages.warning(request, "画像解析は完了しましたが、結果の保存に失敗しました。")

    return render(request, 'index.html', {
        'predictions': predictions,
        'image_data': image_url
    })


# ------------------------------------------------------------------
# 履歴一覧画面（ページネーション付き）
# ------------------------------------------------------------------
def view_data(request):
    """
    解析履歴の一覧表示（ページネーション付き）
    """
    # 作成日時の降順（新しい順）で全取得
    all_results = AnalysisResult.objects.all().order_by('-created_at')
    
    # 検索機能（オプション）
    search_query = request.GET.get('search', '').strip()
    if search_query:
        all_results = all_results.filter(prediction_label__icontains=search_query)
    
    # ページネーション設定
    paginator = Paginator(all_results, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    
    try:
        results = paginator.page(page_number)
    except PageNotAnInteger:
        # ページ番号が整数でない場合は最初のページ
        results = paginator.page(1)
    except EmptyPage:
        # ページ範囲外の場合は最後のページ
        results = paginator.page(paginator.num_pages)
    
    return render(request, 'view_data.html', {
        'results': results,
        'search_query': search_query
    })


# ------------------------------------------------------------------
# データ削除処理
# ------------------------------------------------------------------
@require_http_methods(["POST"])
def delete_data(request, pk):
    """
    解析結果を削除する（画像ファイルも削除）
    
    Args:
        pk: 削除対象のAnalysisResultのID
    """
    result = get_object_or_404(AnalysisResult, pk=pk)
    
    try:
        # delete()メソッドで画像ファイルも自動削除される（モデルでオーバーライド済み）
        result.delete()
        messages.success(request, f"解析結果（ID: {pk}）を削除しました。")
        logger.info(f"解析結果を削除しました: ID={pk}")
    
    except Exception as e:
        messages.error(request, "削除に失敗しました。")
        logger.error(f"削除エラー: {e}")
    
    return redirect('predict:view_data')


# ------------------------------------------------------------------
# 統計情報取得（オプション機能）
# ------------------------------------------------------------------
def get_statistics(request):
    """
    解析統計情報を取得するAPI（将来的な機能拡張用）
    """
    from django.db.models import Avg, Count
    
    total_count = AnalysisResult.objects.count()
    avg_score = AnalysisResult.objects.aggregate(
        avg_score=Avg('prediction_score')
    )['avg_score'] or 0
    
    # 最も多く検出されたラベルTOP5
    top_labels = AnalysisResult.objects.values('prediction_label').annotate(
        count=Count('prediction_label')
    ).order_by('-count')[:5]
    
    return JsonResponse({
        'total_analyses': total_count,
        'average_confidence': round(avg_score, 2),
        'top_labels': list(top_labels),
        'model_name': 'EfficientNetB0'
    })