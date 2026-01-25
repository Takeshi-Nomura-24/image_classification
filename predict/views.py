import io
import json
import os
import numpy as np
import cv2
from django.shortcuts import render, redirect, get_object_or_404
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.conf import settings
from keras.applications.vgg16 import preprocess_input, decode_predictions
from .models import AnalysisResult

# ------------------------------------------------------------------
# ヘルパー関数: ImageNet IDを日本語ラベルに変換
# ------------------------------------------------------------------
def get_japanese_label(class_id):
    """
    JSONファイルからImageNet ID（n04285008等）に対応する日本語名を取得する。
    お手元のJSON構造（リスト形式）に合わせて検索します。
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
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# ------------------------------------------------------------------
# メイン画面（解析実行）
# ------------------------------------------------------------------
def index(request):
    predictions = None
    image_url = None

    if request.method == 'POST' and request.FILES.get('imageFile'):
        # 1. 画像ファイルの取得とOpenCV形式への変換
        file = request.FILES['imageFile']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # 2. VGG16用の前処理 (224x224へリサイズ)
        img_resized = cv2.resize(img, (224, 224))
        x = np.expand_dims(img_resized, axis=0)
        x = preprocess_input(x)

        # 3. AI推論実行 (AppConfigでロード済みのモデルを使用)
        model = apps.get_app_config('predict').model
        preds = model.predict(x)
        results = decode_predictions(preds, top=5)[0]

        # 4. 解析結果の日本語化と整形
        predictions = []
        for class_id, name, prob in results:
            # 日本語ラベル取得を試みる。なければ英語名を整形。
            jp_name = get_japanese_label(class_id) or name.replace('_', ' ')
            
            predictions.append({
                'name': jp_name,
                'prob': f"{prob * 100:.2f}%",
                'raw_prob': prob * 100
            })

        # --- 5. データベースへの保存処理 ---
        top_id, top_name, top_prob = results[0]
        top_jp_name = get_japanese_label(top_id) or top_name.replace('_', ' ')
        
        # ファイルポインタを先頭に戻してから保存
        file.seek(0)
        result_instance = AnalysisResult(
            image=file,
            prediction_label=top_jp_name,
            prediction_score=round(float(top_prob * 100), 2)
        )
        result_instance.save()
        
        # 表示用に保存した画像のURLを取得
        image_url = result_instance.image.url

    return render(request, 'index.html', {
        'predictions': predictions,
        'image_data': image_url
    })

# ------------------------------------------------------------------
# 履歴一覧画面（ページネーション付き）
# ------------------------------------------------------------------
def view_data(request):
    # 作成日時の降順（新しい順）で全取得
    all_results = AnalysisResult.objects.all().order_by('-created_at')
    
    # 1ページに10件表示する設定
    paginator = Paginator(all_results, 10)
    page_number = request.GET.get('page')
    results = paginator.get_page(page_number)
    
    return render(request, 'view_data.html', {'results': results})

# ------------------------------------------------------------------
# データ削除処理
# ------------------------------------------------------------------
def delete_data(request, pk):
    # 該当レコードの取得（なければ404）
    result = get_object_or_404(AnalysisResult, pk=pk)
    
    # サーバー上の物理画像ファイルも消したい場合は以下を有効化
    # result.image.delete()
    
    result.delete()
    return redirect('predict:view_data')


