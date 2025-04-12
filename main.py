import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json

# --- secrets 対応 ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# --- Google Cloud Vision OCR 関数 ---
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

# --- DeepL 翻訳関数 ---
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

# --- UIスタイル カフェ風 ---
st.set_page_config(page_title="Cafe Menu Translator", page_icon="☕", layout="centered")
st.markdown(
    """
    <style>
        .stApp {
            background-image: url("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4");
            background-size: cover;
            background-position: center;
        }
        .title-text {
            background-color: rgba(255, 255, 255, 0.7);
            padding: 1rem;
            border-radius: 10px;
            font-size: 2rem;
            text-align: center;
        }
        .text-block {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Streamlit UI ---
st.markdown("<div class='title-text'>📸 Cafe Menu OCR & 翻訳</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロードされた画像", use_column_width=True)

    st.markdown("<div class='text-block'><strong>🔍 OCR 処理中...</strong></div>", unsafe_allow_html=True)
    text = ocr_with_google_vision(image)

    st.markdown("<div class='text-block'><strong>📝 抽出された日本語テキスト</strong></div>", unsafe_allow_html=True)
    st.text_area("OCR結果", text, height=200)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.markdown("<div class='text-block'><strong>🌍 翻訳結果</strong></div>", unsafe_allow_html=True)
        for line in lines:
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"<div class='text-block'><strong>🍽️ {line}</strong></div>", unsafe_allow_html=True)
            with col2:
                translated = translate_text_deepl(line)
                st.markdown(f"<div class='text-block'>➡️ {translated}</div>", unsafe_allow_html=True)
    else:
        st.warning("テキストが認識されませんでした。画像を確認してください。")