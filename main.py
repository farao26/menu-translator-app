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

# --- APIキー読み込み ---
GOOGLE_CLOUD_VISION_API_KEY = st.secrets["GOOGLE_CLOUD_VISION_API_KEY"]
DEEPL_API_KEY = st.secrets["DEEPL_API_KEY"]
GOOGLE_CUSTOM_SEARCH_API_KEY = st.secrets["GOOGLE_CUSTOM_SEARCH_API_KEY"]
GOOGLE_CSE_ID = st.secrets["GOOGLE_CSE_ID"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- Gemini API 初期化 ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-pro")

# --- OCR関数（Google Cloud Vision） ---
def ocr_with_google_vision(image):
    def remove_prices(text):
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = re.sub(r'[\u00A5\uFFE5]?\d{2,5}円?', '', line)
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
    return ""

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
    return text

# --- Google画像検索 ---
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

# --- Geminiで料理の情報取得 ---
def get_dish_info_from_gemini(name_en):
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

# --- UI Setup ---
st.set_page_config(layout="wide")
st.markdown("""
<style>
body {
    background: linear-gradient(145deg, #001f3f, #1a1a2e);
    color: white;
    font-family: 'Helvetica Neue', sans-serif;
}
.card {
    transition: transform .2s;
    background-color: #00334e;
    color: #fff;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.card:hover {
    transform: scale(1.03);
    background-color: #004b6b;
}
a {
    color: #66ccff;
}
</style>
""", unsafe_allow_html=True)

st.title("🍷 Elegant Menu Translator")
st.write("Upload a menu image to translate and get dish info in English.")

uploaded_file = st.file_uploader("📸 Upload menu image", type=["jpg", "jpeg", "png"])

if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Menu", use_column_width=True)
    st.markdown("---")

    text = ocr_with_google_vision(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if lines:
        st.subheader("🌍 Translations and Dish Info")
        for line in lines:
            translated = translate_text_deepl(line)
            st.session_state.history.append((line, translated))

            image_url = get_google_image(f"Japanese {translated} food", GOOGLE_CUSTOM_SEARCH_API_KEY, GOOGLE_CSE_ID)
            gpt_info = get_dish_info_from_gemini(translated)

            if gpt_info == "NOT_A_DISH":
                continue

            col1, col2 = st.columns([1, 2])
            with col1:
                if image_url:
                    st.image(image_url, width=300)
                else:
                    st.write("No image found")
            with col2:
                st.markdown(f"""
                <div style='background-color:#f8f8f8;color:#222;padding:15px;border-radius:10px;border: 1px solid #ccc;font-size:15px;line-height:1.6;box-shadow:2px 2px 5px rgba(0,0,0,0.2);'>
                <b style='color:#004466;'>Gemini Insight</b><br>
                <pre style='white-space:pre-wrap;font-family:inherit;background:none;border:none;'>{gpt_info}</pre>
                </div>
                """, unsafe_allow_html=True)

if st.session_state.history:
    if st.button("📂 Save Translation History"):
        filename = f"translation_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for original, translated in st.session_state.history:
                f.write(f"{original} => {translated}\n")
        with open(filename, "rb") as f:
            st.download_button("⬇️ Download", f, file_name=filename)