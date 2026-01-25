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
# --- 修正: MobileNetV2用の関数をインポート ---
from keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
from .models import AnalysisResult

# ------------------------------------------------------------------
# メイン画面（解析実行）
# ------------------------------------------------------------------
def index(request):
    predictions = None
    image_url = None

    if request.method == 'POST' and request.FILES.get('imageFile'):
        # 1. 画像ファイルの取得
        file = request.FILES['imageFile']
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # 2. MobileNetV2用の前処理
        img_resized = cv2.resize(img, (224, 224))
        x = np.expand_dims(img_resized, axis=0)
        x = preprocess_input(x)

        # 3. AI推論実行
        model = apps.get_app_config('predict').model
        preds = model.predict(x)
        results = decode_predictions(preds, top=5)[0]

        # 4. 解析結果の整形（英語名をそのまま使用）
        predictions = []
        for class_id, name, prob in results:
            # 修正: 日本語ラベル取得をやめ、アンダースコアをスペースに置換するだけにします
            display_name = name.replace('_', ' ')
            
            predictions.append({
                'name': display_name,
                'prob': f"{prob * 100:.2f}%",
                'raw_prob': prob * 100
            })

        # --- 5. データベースへの保存処理 ---
        top_id, top_name, top_prob = results[0]
        # 修正: 保存する名前も英語名にする
        save_name = top_name.replace('_', ' ')
        
        file.seek(0)
        result_instance = AnalysisResult(
            image=file,
            prediction_label=save_name,
            prediction_score=round(float(top_prob * 100), 2)
        )
        result_instance.save()
        
        image_url = result_instance.image.url

    return render(request, 'index.html', {
        'predictions': predictions,
        'image_data': image_url
    })

# ...（以降の view_data, delete_data は変更なし） ...

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


