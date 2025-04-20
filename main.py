import streamlit as st
from PIL import Image
import io
import os
import base64
import requests
import json
import re
from datetime import datetime
import google.generativeai as genai

# --- Secrets ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GOOGLE_CUSTOM_SEARCH_API_KEY = st.secrets["GOOGLE_CUSTOM_SEARCH_API_KEY"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- Gemini Init ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# --- OCR Function ---
def ocr_with_google_vision(image):
    def remove_prices(text):
        lines = text.split('\n')
        return '\n'.join([re.sub(r'[\u00A5\uFFE5]?[0-9]{2,5}\s?yen|\u5186?', '', line).strip() for line in lines if line.strip()])

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
    return ""

# --- DeepL Translation ---
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
    return response.json()["translations"][0]["text"] if response.status_code == 200 else ""

# --- Gemini Info ---
def get_dish_info_with_gemini(dish_name):
    prompt = f'''
Is "{dish_name}" a food dish? If yes, return the following:

1. Common Ingredients (3–5 items, short, no full sentences)
2. Potential Allergens (start with "Generally includes..." and list)
3. Short Description (within 50 characters)
   - If the dish is well-known (more than 10 search hits): write only description.
   - If rare: add this sentence at the end: "This may be an unexpectedly interesting dish."
4. History or Trivia (within 50 characters)

If not a food, just answer: NOT_A_DISH
'''
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini Error: {str(e)}"

# --- Google Image Search ---
def get_google_image(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CUSTOM_SEARCH_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "searchType": "image",
        "num": 1,
        "safe": "high",
        "imgType": "photo"
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        if "items" in data:
            return data["items"][0]["link"]
    return None

# --- UI ---
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .card {
        background-color: #002b36;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: scale(1.02);
        background-color: #003c4d;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍽️ Elegant Menu Translator")
st.caption("Powered by Google OCR + DeepL + Gemini")

uploaded_file = st.file_uploader("📷 メニュー画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="アップロード画像", use_column_width=True)

    raw_text = ocr_with_google_vision(image)
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if lines:
        st.subheader("🔍 翻訳と補足情報")
        for line in lines:
            translated = translate_text_deepl(line)
            info = get_dish_info_with_gemini(translated)

            if info == "NOT_A_DISH":
                continue

            image_url = get_google_image(f"Japanese food {translated}")
            with st.container():
                hover_info = info.replace("\n", "<br>")
                st.markdown(f"""
                <div class="card" title="{hover_info}">
                    <b style='color:#ffd700;font-size:18px;'>{line}</b><br>
                    <span style='color:#66ccff;font-size:16px;'>➡️ {translated}</span><br>
                    {f'<img src="{image_url}" width="300">' if image_url else '<i>No image found</i>'}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("テキストが抽出できませんでした。画像をご確認ください。")
         