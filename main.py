import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json

# SecretsからAPIキーを取得
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# OCR処理（Google Cloud Vision API）
def ocr_with_google_vision(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [
            {
                "image": {"content": img_base64},
                "features": [{"type": "TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["ja"]}
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        annotations = response.json()["responses"][0].get("textAnnotations")
        if annotations:
            return annotations[0]["description"]
        else:
            return ""
    else:
        return f"[Error] {response.status_code}: {response.text}"

# 翻訳（DeepL API）
def translate_text_deepl(text, source_lang='JA', target_lang='EN'):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target_lang,
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        return f"[Error] {response.status_code}: {response.text}"

# ページ設定とCSSスタイル
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to bottom, #000428, #004e92);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stTextArea textarea {
        background-color: #1a1a2e;
        color: white;
    }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 8px;
    }
    .card {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown("<h1 style='color:#ffffff; text-align:center;'>🍷 Elegant Menu Translator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#cccccc;'>Translate menus in style - Japanese to English 🇯🇵➡️🇬🇧</p>", unsafe_allow_html=True)

# ファイルアップロード
uploaded_file = st.file_uploader("📸 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.markdown("---")
    st.subheader("🔍 OCR抽出結果（日本語）")
    text = ocr_with_google_vision(image)
    st.text_area("OCR結果", text, height=200)

    # 行ごとに翻訳してカード風に表示
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 翻訳結果")
        for line in lines:
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='card'><strong>{line}</strong></div>", unsafe_allow_html=True)
                with col2:
                    translated = translate_text_deepl(line)
                    st.markdown(f"<div class='card'>➡️ {translated}</div>", unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")
