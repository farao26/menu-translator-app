import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import google.generativeai as genai
from dotenv import load_dotenv

# --- 環境変数の読み込み（Secrets.tomlを想定） ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- Gemini 初期化 ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- OCR with Google Vision ---
def ocr_with_google_vision(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_CLOUD_VISION_API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [{
            "image": {"content": img_base64},
            "features": [{"type": "TEXT_DETECTION"}],
            "imageContext": {"languageHints": ["ja"]}
        }]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        annotations = response.json()["responses"][0].get("textAnnotations")
        return annotations[0]["description"] if annotations else ""
    else:
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
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    else:
        return f"[Error] {response.status_code}: {response.text}"

# --- Dish Check & Info (Gemini) ---
def get_dish_info_with_gemini(name_en):
    prompt = f"""
Is "{name_en}" a food dish? If it is, answer in the following format:

1. Common Ingredients (3–5)
2. Potential Allergens (start with "Generally includes...")
3. Short Description (within 50 characters)
4. History / Trivia (within 50 characters)

If not a food, just answer: "NOT_A_DISH"
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# --- UIセットアップ ---
st.set_page_config(layout="wide", page_title="Menu Translator (Gemini)")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 320px;
        background-color: #444;
        color: #fff;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 1;
        bottom: 125%; 
        left: 50%;
        margin-left: -160px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 14px;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍷 Elegant Menu Translator")
st.caption("Powered by Google Vision, DeepL & Gemini")

uploaded_file = st.file_uploader("📸 Upload Menu Image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="📷 Uploaded Image", use_column_width=True)

    ocr_text = ocr_with_google_vision(image)
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 Translation & Hover Info")
        for line in lines:
            translated = translate_text_deepl(line)
            dish_info = get_dish_info_with_gemini(translated)

            if "NOT_A_DISH" not in dish_info:
                # ホバー付きカード表示
                html = f"""
                <div class="tooltip">
                    <span style="font-weight:bold; color:#ffd700; font-size:18px;">🍽️ {translated}</span>
                    <div class="tooltiptext">{dish_info.replace('\n', '<br>')}</div>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)
            else:
                # 非料理の翻訳は表示しない or ログ出力だけでもOK
                pass
    else:
        st.warning("画像から文字を検出できませんでした。")
         