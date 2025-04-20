import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import re
from datetime import datetime
# SecretsからAPIキー取得
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GOOGLE_CUSTOM_SEARCH_API_KEY = st.secrets["GOOGLE_CUSTOM_SEARCH_API_KEY"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
# OCR (Google Vision API)
def ocr_with_google_vision(image):
    def remove_prices(text):
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'[¥￥]?\d{2,5}円?', '', line)
            if line.strip():
                cleaned_lines.append(line.strip())
        return '\n'.join(cleaned_lines)
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
            raw_text = annotations[0]["description"]
            return remove_prices(raw_text)
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
# Google画像検索
def get_google_image(query, api_key, cse_id):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "searchType": "image",
        "num": 1,
        "safe": "high",
        "imgType": "photo"
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        results = response.json()
        if "items" in results:
            return results["items"][0]["link"]
    return None
# UIデザイン
st.set_page_config(layout="wide", page_title="Elegant Menu Translator")
st.markdown("""
    <style>
    body {
        background: linear-gradient(145deg, #001F3F, #1A1A2E);
        color: white;
    }
    .card {
        transition: transform .2s;
        background-color: #00334E;
        color: #fff;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .card:hover {
        transform: scale(1.05);
        background-color: #004B6B;
    }
    a {
        color: #66CCFF;
    }
    </style>
""", unsafe_allow_html=True)
st.title(":wine_glass: Elegant Menu Translator")
st.caption("Upload a menu image, translate to English, and see matching dish images!")
uploaded_file = st.file_uploader(":camera_with_flash: Upload menu image", type=["jpg", "jpeg", "png"])
# 履歴管理
if "history" not in st.session_state:
    st.session_state.history = []
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    st.markdown("---")
    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        st.subheader(":earth_africa: Translation Results (Hoverable Cards)")
        for line in lines:
            translated = translate_text_deepl(line)
            st.session_state.history.append((line, translated))
            image_url = get_google_image(f"Japanese {translated} food", GOOGLE_CUSTOM_SEARCH_API_KEY, GOOGLE_CSE_ID)
            if image_url:
                st.markdown(f"""
                <div class="card">
                    <b>{line}</b><br>
                    <span style='color:#ccffcc;'>:arrow_right: {translated}</span><br>
                    <img src="{image_url}" width="300"><br>
                    <a href="{image_url}" target="_blank">:mag: View dish image</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card">
                    <b>{line}</b><br>
                    <span style='color:#ccffcc;'>:arrow_right: {translated}</span><br>
                    <i>:mag: No image found</i>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No text recognized. Please check the image.")
# 翻訳履歴保存
if st.session_state.history:
    if st.button(":floppy_disk: Save translation history"):
        filename = f"translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for original, translated in st.session_state.history:
                f.write(f"{original} => {translated}\n")
        with open(filename, "rb") as f:
            st.download_button(":arrow_down: Download", f, file_name=filename)
            