import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from openai import OpenAI

# --- SecretsからAPIキー取得 ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# --- OpenAI 初期化 ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- OCR with Google Cloud Vision ---
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

# --- DeepL 翻訳 ---
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

# --- GPTによる料理情報生成（英語出力） ---
def get_dish_info_from_gpt(dish_name):
    prompt = f"""
Dish Name: "{dish_name}"
Please provide the following:

1. Commonly used ingredients (3-5 items, concise).
2. Possible allergens. Begin with "Commonly includes...".
3. Short description within 50 characters.
   - If the dish is well-known (many web results), just give a simple description.
   - If the dish is rare (few web results), end with "It might be something unexpected."
4. Brief history or trivia (within 50 characters).
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a culinary expert for international and Japanese cuisine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT Error: {str(e)}"

# --- UI 設定 ---
st.set_page_config(layout="wide", page_title="Menu Translator")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stTextArea textarea {
        background-color: #1a1a2e;
        color: #fff;
    }
    .stButton>button {
        background-color: #003366;
        color: white;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- アプリUI ---
st.title("🍷 Elegant Menu Translator")
st.caption("Translate with Style — Smart. Bilingual. Beautiful.")
st.write("Upload a menu image to translate and get culinary insights.")

uploaded_file = st.file_uploader("📸 Upload your menu image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 Translation & Culinary Insight")
        for line in lines:
            translated = translate_text_deepl(line)

            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    info = get_dish_info_from_gpt(translated)
                    hover_html = f"""
                    <span style='font-size:18px; font-weight:bold; color:#ffd700;' title="{info}">
                        {line}
                    </span><br>
                    <span style='color:#66ccff; font-size:16px;'>➡️ {translated}</span>
                    """
                    st.markdown(hover_html, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"<div style='background:#111;padding:8px;border-radius:8px;color:#ddd;font-size:14px;'><pre>{info}</pre></div>", unsafe_allow_html=True)
    else:
        st.warning("No text detected. Please check the image.")
           