import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv

# Secrets対応の環境変数読み込み（Streamlit Cloud用）
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]

# Google Cloud Vision API を使って OCR を実行する関数
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

# DeepL API を使った翻訳関数
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

# Streamlit アプリ本体
def main():
    st.markdown("""
        <style>
            body {
                background-color: #0b1f3a;
                color: white;
                font-family: 'Helvetica Neue', sans-serif;
            }
            .block-container {
                padding: 2rem 1rem;
            }
            .title-text {
                font-size: 2.5rem;
                font-weight: bold;
                color: #f0f8ff;
                text-align: center;
                margin-bottom: 1rem;
            }
            .caption-text {
                text-align: center;
                font-size: 1rem;
                margin-bottom: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='title-text'>📸 Menu OCR & 翻訳</div>", unsafe_allow_html=True)
    st.markdown("<div class='caption-text'>画像から日本語テキストを抽出し、英語に翻訳します</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("画像をアップロードしてください", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた画像", use_column_width=True)

        st.subheader("🔍 OCR結果（Google Cloud Vision）")
        text = ocr_with_google_vision(image)
        st.text_area("抽出された日本語テキスト", text, height=200)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            st.subheader("🌍 DeepL翻訳（左右に並べて表示）")
            for line in lines:
                with st.container():
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f"<div style='background-color:#1a2c4e;padding:10px;border-radius:10px;'>🍽️ {line}</div>", unsafe_allow_html=True)
                    with col2:
                        translated = translate_text_deepl(line)
                        st.markdown(f"<div style='background-color:#32476e;padding:10px;border-radius:10px;'>➡️ {translated}</div>", unsafe_allow_html=True)
        else:
            st.warning("テキストが認識されませんでした。画像を確認してください。")

if __name__ == "__main__":
    main()
    