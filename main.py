import streamlit as st
from PIL import Image
import io
import base64
import requests
import json
import re
from datetime import datetime

# --- SecretsからAPIキー取得 ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GOOGLE_CUSTOM_SEARCH_API_KEY = st.secrets["GOOGLE_CUSTOM_SEARCH_API_KEY"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]

# --- OCR (Google Vision API) ---
def ocr_with_google_vision(image):
    def remove_prices(text):
        lines = text.split('\n')
        cleaned_lines = [re.sub(r'[\u00A5\uFFE5]?\d{2,5}円?', '', line).strip() for line in lines if line.strip()]
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
        return remove_prices(annotations[0]["description"]) if annotations else ""
    return f"[Error] {response.status_code}: {response.text}"

# --- DeepL翻訳 ---
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
    return response.json()["translations"][0]["text"] if response.status_code == 200 else text

# --- Google画像検索 ---
def get_google_image(query, api_key, cse_id):
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "searchType": "image",
        "num": 1,
        "safe": "high",
        "imgType": "photo"
    }
    response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
    if response.status_code == 200:
        items = response.json().get("items", [])
        return items[0]["link"] if items else None
    return None

# --- UIセットアップ ---
st.set_page_config(layout="wide", page_title="Elegant Menu Translator")
st.markdown("""
    <style>
    body {
        background: linear-gradient(145deg, #f9f5f0, #efe8dc);
        color: #3e3e3e;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .card {
        transition: transform .2s;
        background-color: #fff9f2;
        color: #3e3e3e;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .card:hover {
        transform: scale(1.03);
        background-color: #fdf5e6;
    }
    a {
        color: #8b5e3c;
    }
    </style>
""", unsafe_allow_html=True)

st.title("\U0001F374 Elegant Menu Translator")
st.caption("Upload a menu image, translate to English, and explore dish images!")

uploaded_file = st.file_uploader("\U0001F4F7 Upload menu image", type=["jpg", "jpeg", "png"])

if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    st.markdown("---")

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("\U0001F30D Translated Dishes")
        for line in lines:
            translated = translate_text_deepl(line)
            st.session_state.history.append((line, translated))

            query = f"Japanese cuisine {line} {translated}"
            image_url = get_google_image(query, GOOGLE_CUSTOM_SEARCH_API_KEY, GOOGLE_CSE_ID)

            st.markdown(f"""
            <div class="card">
                <b>{line}</b><br>
                <span style='color:#8b5e3c;'>➡️ {translated}</span><br>
                {'<img src="' + image_url + '" width="300">' if image_url else '<i>No image found</i>'}<br>
                {'<a href="' + image_url + '" target="_blank">🔍 View dish image</a>' if image_url else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No text recognized. Please check the image.")

# --- 翻訳履歴の保存 ---
if st.session_state.history:
    if st.button("💾 Save translation history"):
        filename = f"translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for original, translated in st.session_state.history:
                f.write(f"{original} => {translated}\n")
        with open(filename, "rb") as f:
            st.download_button("⬇️ Download", f, file_name=filename)

