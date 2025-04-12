import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from streamlit_extras.let_it_rain import rain

# 環境変数読み込み（Streamlit CloudではSecretsを使用）
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# 動的なエフェクト（上品なグリッター）
rain(emoji="✨", font_size=20, falling_speed=3, animation_length="infinite")

# 背景とフォントのカスタムCSS
st.markdown("""
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1600891964599-f61ba0e24092");
        background-size: cover;
        background-position: center;
        position: relative;
        color: #f5f5f5;
        font-family: 'Georgia', serif;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: -1;
    }
    .title {
        font-size: 48px;
        font-weight: bold;
        margin-top: 1rem;
    }
    .section-title {
        font-size: 28px;
        margin-top: 2rem;
        color: #ffdd99;
    }
    </style>
""", unsafe_allow_html=True)

# OCR with Google Cloud Vision

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

# DeepL Translation

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

# Streamlit UI
st.markdown("<div class='title'>🌟 Menu OCR & Translator</div>", unsafe_allow_html=True)
st.write("高級レストランのメニューを画像から翻訳するアプリ")

uploaded_file = st.file_uploader("📷 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="🖼️ アップロード画像", use_column_width=True)

    st.markdown("<div class='section-title'>🔍 OCR結果</div>", unsafe_allow_html=True)
    text = ocr_with_google_vision(image)
    st.text_area("抽出された日本語テキスト", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.markdown("<div class='section-title'>🌐 翻訳結果</div>", unsafe_allow_html=True)
        for line in lines:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"<div style='font-size:18px; font-weight:bold;'>🍽️ {line}</div>", unsafe_allow_html=True)
            with col2:
                translated = translate_text_deepl(line)
                st.markdown(f"<div style='font-size:18px; color:#ffeecc;'>➡️ {translated}</div>", unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")
