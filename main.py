import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI
from streamlit_extras.animated_headline import animated_headline

# --- SecretsからAPIキー取得 ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# --- OpenAI初期化 ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Google Cloud Vision OCR ---
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

# --- OpenAI：これは料理名か？ ---
def is_dish_name(text):
    prompt = f"Is '{text}' likely to be the name of a Japanese dish or food item? Answer only 'yes' or 'no'."
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        result = response.choices[0].message.content.strip().lower()
        return result.startswith("yes")
    except Exception as e:
        return False

# --- OpenAI：料理の説明生成（英語）---
def get_dish_info_from_gpt(dish_name):
    prompt = f"""
Dish Name: "{dish_name}"
1. Commonly used ingredients (3~5 items)
2. Possible allergenic ingredients
3. Simple description (within 50 characters; add note if rare)
4. History or trivia (within 50 characters)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Japanese cuisine."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT Error: {str(e)}"

# --- UIスタイル ---
st.set_page_config(layout="wide", page_title="Menu Translator")
st.markdown(
    """
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
    """,
    unsafe_allow_html=True
)

# --- アプリUI ---
animated_headline("🍷 Elegant Menu Translator", ["Translate with Style", "Smart. Bilingual. Beautiful."])
st.write("Upload a Japanese menu image to translate dish names and view details.")

uploaded_file = st.file_uploader("📸 Upload a menu image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 Translations & Details (only for food items)")
        for line in lines:
            if is_dish_name(line):
                translated = translate_text_deepl(line)
                with st.container():
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.markdown(f"<div style='font-size:18px; font-weight:bold; color:#ffd700;'>{line}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='color:#66ccff; font-size:16px;'>➡️ {translated}</div>", unsafe_allow_html=True)
                    with col2:
                        with st.expander("🍽️ Dish Details"):
                            info = get_dish_info_from_gpt(translated)
                            st.markdown(f"<pre style='background-color:#222; color:#eee; border-radius:8px; padding:10px;'>{info}</pre>", unsafe_allow_html=True)
            else:
                continue
    else:
        st.warning("No text detected. Please try another image.")
          