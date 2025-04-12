import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from streamlit_extras.let_it_rain import rain
from streamlit_extras.app_logo import add_logo
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.colored_header import colored_header

# Secrets から読み込み
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# CSS カスタマイズでカフェ風デザイン
st.markdown("""
    <style>
    body {
        background-color: #fdf6f0;
        color: #4b3832;
    }
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1509042239860-f550ce710b93");
        background-size: cover;
        background-position: center;
    }
    .title {
        font-family: 'Courier New', monospace;
        font-size: 2.8em;
        font-weight: bold;
        color: #3e2723;
        text-align: center;
        padding: 1rem;
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 10px;
    }
    .result-box {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">📸 Cafe Menu OCR & 翻訳</div>', unsafe_allow_html=True)

# 画像アップロード
uploaded_file = st.file_uploader("カフェのメニュー画像をアップロードしてください ☕", type=["jpg", "jpeg", "png"])

# OCR 関数

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

# DeepL翻訳

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

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="🍽️ アップロードされた画像", use_column_width=True)

    with st.spinner("🔍 OCR解析中..."):
        text = ocr_with_google_vision(image)

    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.subheader("📝 抽出された日本語テキスト")
    st.text_area("OCR結果", text, height=200)
    st.markdown('</div>', unsafe_allow_html=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader("🌍 DeepL 翻訳結果")
        for line in lines:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🍵 {line}**")
            with col2:
                translated = translate_text_deepl(line)
                st.markdown(f"➡️ {translated}")
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")

    rain(emoji="☕", font_size=30, falling_speed=5, animation_length="infinite")