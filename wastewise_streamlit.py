"""
WasteWise Streamlit App - With FiftyOne Analytics
Single-file waste classification app with leaderboard, badges, and FiftyOne insights
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
import base64
from PIL import Image
import io
import requests
from anthropic import Anthropic
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load environment variables
load_dotenv()

# ============================================
# API KEY - works locally AND on Streamlit Cloud
# ============================================
def get_api_key():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "")

# ============================================
# FIFTYONE INTEGRATION (ANALYTICS)
# ============================================

def init_fiftyone_dataset():
    try:
        import fiftyone as fo
        if "WasteWise_Submissions" in fo.list_datasets():
            return fo.load_dataset("WasteWise_Submissions")
        dataset = fo.Dataset("WasteWise_Submissions")
        return dataset
    except Exception as e:
        return None

def add_submission_to_fiftyone(image_base64, item_name, bin_type, confidence, city, username):
    try:
        import fiftyone as fo
        dataset = init_fiftyone_dataset()
        if dataset is None:
            return False
        image_data = base64.b64decode(image_base64)
        image_path = f"/tmp/wastewise_{datetime.now().timestamp()}.jpg"
        with open(image_path, 'wb') as f:
            f.write(image_data)
        sample = fo.Sample(filepath=image_path)
        sample['item'] = item_name
        sample['bin_type'] = bin_type
        sample['confidence'] = confidence
        sample['city'] = city
        sample['username'] = username
        sample['timestamp'] = datetime.now().isoformat()
        sample['verified'] = False
        dataset.add_sample(sample)
        dataset.save()
        return True
    except Exception as e:
        print(f"FiftyOne add error: {e}")
        return False

def get_analytics_data():
    data = load_data()
    submissions = []
    for username, user in data["users"].items():
        if "submissions" in user:
            for sub in user["submissions"]:
                submissions.append({
                    "username": username,
                    "city": user["city"],
                    "item": sub.get("item", "Unknown"),
                    "bin": sub.get("bin", "Unknown"),
                    "confidence": sub.get("confidence", 0),
                    "timestamp": sub.get("timestamp", ""),
                    "verified": sub.get("verified", False)
                })
    return pd.DataFrame(submissions) if submissions else pd.DataFrame()

def get_city_statistics(city):
    df = get_analytics_data()
    if df.empty or len(df[df['city'] == city]) == 0:
        return None
    city_df = df[df['city'] == city]
    stats = {
        "total_submissions": len(city_df),
        "recycling_count": len(city_df[city_df['bin'] == 'recycling']),
        "compost_count": len(city_df[city_df['bin'] == 'compost']),
        "landfill_count": len(city_df[city_df['bin'] == 'landfill']),
        "special_count": len(city_df[city_df['bin'] == 'special']),
        "avg_confidence": city_df['confidence'].mean(),
        "common_items": city_df['item'].value_counts().head(5).to_dict(),
        "verified_rate": len(city_df[city_df['verified'] == True]) / len(city_df) * 100 if len(city_df) > 0 else 0
    }
    return stats

# ============================================
# DROP-OFF LOCATIONS
# ============================================

DROPOFF_LOCATIONS = {
    "Tempe": [
        {"name": "Tempe Transfer Station", "lat": 33.4148, "lon": -111.9290, "accepts": "Electronics, Batteries, Paint, Chemicals"},
        {"name": "Home Depot Tempe", "lat": 33.4255, "lon": -111.9400, "accepts": "Batteries, CFLs, Paint"},
        {"name": "Best Buy Tempe Marketplace", "lat": 33.4285, "lon": -111.9712, "accepts": "Electronics, Cables, Phones, Batteries"},
    ],
    "Phoenix": [
        {"name": "Phoenix HHW Facility – 27th Ave", "lat": 33.4942, "lon": -112.0908, "accepts": "Paint, Chemicals, Electronics, Batteries"},
        {"name": "Best Buy Phoenix", "lat": 33.5085, "lon": -112.0678, "accepts": "Electronics, Cables, Phones"},
    ],
    "Mesa": [
        {"name": "Mesa HHW Drop-off", "lat": 33.4152, "lon": -111.8315, "accepts": "Paint, Chemicals, Batteries, Electronics"},
    ],
    "Scottsdale": [
        {"name": "Scottsdale Recycling Center", "lat": 33.4942, "lon": -111.9261, "accepts": "Electronics, Batteries, Paint"},
    ],
}

def show_dropoff_map(city: str):
    city_key = city.split(",")[0].strip()
    locations = DROPOFF_LOCATIONS.get(city_key, DROPOFF_LOCATIONS["Tempe"])
    st.markdown("""
    <div style='background:#fff8e1;border-left:4px solid #f59e0b;padding:14px 18px;border-radius:6px;margin:12px 0;'>
        <h4 style='color:#92400e;margin:0 0 4px;'>⚠️ Special Disposal Required</h4>
        <p style='color:#78350f;margin:0;font-size:0.9em;'>Do NOT put this in regular bins. Drop off at one of these locations.</p>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("📍 Nearest Drop-off Locations")
    map_df = pd.DataFrame([{"lat": l["lat"], "lon": l["lon"]} for l in locations])
    st.map(map_df, zoom=12)
    for loc in locations:
        st.markdown(f"""
        <div style='background:#f0f7f4;border:1px solid #d4e8e0;border-left:3px solid #2D6A4F;
                    padding:10px 14px;border-radius:6px;margin:6px 0;'>
            <strong style='color:#1B4332;'>📦 {loc["name"]}</strong><br>
            <span style='color:#555;font-size:0.88em;'>Accepts: {loc["accepts"]}</span>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# PAGE CONFIG & STYLING
# ============================================

st.set_page_config(
    page_title="WasteWise",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    :root {
        --primary: #1B4332;
        --primary-light: #2D6A4F;
        --accent: #52B788;
        --bg-light: #f0f7f4;
        --border: #d4e8e0;
    }

    body, .stApp { background-color: #f0f7f4; }

    /* ── FIX: all inputs readable on dark bg ── */
    input, textarea, [data-baseweb="input"] input,
    .stTextInput input, .stPasswordInput input {
        color: #ffffff !important;
        caret-color: #ffffff !important;
    }

    /* ── FIX: selectbox text ── */
    .stSelectbox div[data-baseweb="select"] div {
        color: #1B4332 !important;
        background-color: #ffffff !important;
    }

    /* ── Buttons always white text ── */
    .stButton > button {
        background: #2D6A4F !important;
        color: #ffffff !important;
        border: none;
        border-radius: 4px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover { background: #1B4332 !important; }

    /* ── Metrics ── */
    .stMetric { background: #ffffff; padding: 15px; border-radius: 6px; border: 1px solid #d4e8e0; }
    .stMetric label { color: #555555 !important; font-weight: 600 !important; }

    /* ── Cards ── */
    .card { background: #ffffff; border-radius: 6px; padding: 20px; margin: 10px 0; border: 1px solid #d4e8e0; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #d4e8e0; }
    [data-testid="stSidebar"] * { color: #1B4332 !important; }

    /* ── Global text ── */
    h1, h2, h3, h4, h5, h6 { color: #1B4332 !important; }
    p, li { color: #333333 !important; }
    label { color: #1B4332 !important; }
    .stMarkdown p { color: #333333 !important; }

    /* ── File uploader ── */
    [data-testid="stFileUploadDropzone"] span { color: #ffffff !important; }

    /* ── Alert ── */
    .stAlert { border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA STORAGE
# ============================================

DATA_FILE = "wastewise_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"users": {}, "leaderboard": [], "waste_items": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ============================================
# AUTO-SAVE HELPER
# ============================================

def auto_save_submission(result):
    """Save classification result immediately — no button needed"""
    data = load_data()
    user = data["users"][st.session_state.username]

    user["totalPoints"] += result["points"]
    user["totalItemsSorted"] += 1
    user["stats"]["co2Saved"] += result["environmentalImpact"]["co2"]
    user["stats"]["waterSaved"] += result["environmentalImpact"]["water"]
    user["stats"]["treesSaved"] += result["environmentalImpact"]["trees"]

    submission = {
        "timestamp": datetime.now().isoformat(),
        "item": result["item"],
        "bin": result["bin"],
        "confidence": result["confidence"],
        "verified": False
    }
    if "submissions" not in user:
        user["submissions"] = []
    user["submissions"].append(submission)

    for entry in data["leaderboard"]:
        if entry["username"] == st.session_state.username:
            entry["totalPoints"] = user["totalPoints"]
            entry["totalItemsSorted"] = user["totalItemsSorted"]
            entry["badges"] = user["badges"]
            break

    save_data(data)
    update_streak(st.session_state.username)
    check_badges(st.session_state.username)

# ============================================
# AUTHENTICATION
# ============================================

def init_user_session():
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_city" not in st.session_state:
        st.session_state.user_city = None
    if "last_saved_item" not in st.session_state:
        st.session_state.last_saved_item = None

def register_user(username, city):
    data = load_data()
    if username in data["users"]:
        return False, "Username already exists"
    data["users"][username] = {
        "city": city, "totalPoints": 0, "totalItemsSorted": 0,
        "currentStreak": 0, "longestStreak": 0,
        "joinedAt": datetime.now().isoformat(),
        "stats": {"co2Saved": 0.0, "waterSaved": 0.0, "treesSaved": 0.0},
        "badges": [], "lastActivityDate": None, "submissions": []
    }
    data["leaderboard"].append({
        "username": username, "city": city,
        "totalPoints": 0, "totalItemsSorted": 0, "badges": []
    })
    save_data(data)
    return True, "Registration successful!"

def login_user(username):
    data = load_data()
    if username not in data["users"]:
        return False, "Username not found"
    return True, data["users"][username]

# ============================================
# WASTE CLASSIFICATION
# ============================================

def classify_waste(image_base64, city: str, media_type: str = "image/jpeg"):
    try:
        api_key = get_api_key()
        if not api_key:
            st.error("⚠️ API key not found. Add ANTHROPIC_API_KEY to .env or Streamlit secrets.")
            return None

        client = Anthropic(api_key=api_key)
        system_prompt = f"""You are WasteWise, a waste disposal expert for {city}.
Key rules for Tempe/Phoenix AZ: curbside recycling YES, curbside composting NO, hazardous waste needs special drop-off at city HHW facilities. Pizza boxes go in recycling ONLY if not heavily soiled. Plastic bags go to store drop-off, NOT curbside recycling.
Respond ONLY in valid JSON with no markdown backticks:
{{
  "item": "short item name (max 4 words)",
  "bin": "recycling or compost or landfill or special",
  "confidence": 0.0,
  "reason": "one clear sentence explaining why",
  "prep": "one sentence on what to do before disposing",
  "impact": "one sentence on environmental impact of correct disposal"
}}"""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system_prompt,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': image_base64}},
                    {'type': 'text', 'text': 'Classify this waste item and tell me how to dispose of it properly.'}
                ]
            }]
        )

        response_text = message.content[0].text
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        result = json.loads(response_text)
        base_points = {"recycling": 100, "compost": 120, "landfill": 25, "special": 150}
        result["points"] = int(base_points.get(result["bin"], 50) * result["confidence"])
        result["environmentalImpact"] = {
            "co2": 2.5 if result["bin"] == "recycling" else (0.5 if result["bin"] == "compost" else 0.1),
            "water": 5 if result["bin"] == "recycling" else (2 if result["bin"] == "compost" else 0.5),
            "trees": 0.001 if result["bin"] == "recycling" else (0.005 if result["bin"] == "compost" else 0)
        }
        return result

    except Exception as e:
        st.error(f"Classification error: {str(e)}")
        return None

# ============================================
# POINTS & BADGES
# ============================================

def calculate_points(bin_type: str, confidence: float):
    base_points = {"recycling": 100, "compost": 120, "landfill": 25, "special": 150}
    return int(base_points.get(bin_type, 50) * confidence)

def check_badges(username: str):
    data = load_data()
    user = data["users"][username]
    badges_to_check = [
        {"id": "first_sort", "condition": user["totalItemsSorted"] >= 1, "name": "🎖️ First Step"},
        {"id": "quick_starter", "condition": user["totalItemsSorted"] >= 10, "name": "🎖️ Quick Starter"},
        {"id": "eco_warrior", "condition": user["totalItemsSorted"] >= 50, "name": "🎖️ Eco Warrior"},
        {"id": "legendary_sorter", "condition": user["totalItemsSorted"] >= 100, "name": "🎖️ Legendary Sorter"},
        {"id": "week_streak", "condition": user["longestStreak"] >= 7, "name": "🔥 7-Day Streak"},
        {"id": "month_streak", "condition": user["longestStreak"] >= 30, "name": "🔥 30-Day Legend"},
    ]
    current_badges = [b["id"] for b in user["badges"]]
    for badge in badges_to_check:
        if badge["condition"] and badge["id"] not in current_badges:
            user["badges"].append({"id": badge["id"], "name": badge["name"]})
            st.success(f"🎉 Unlocked badge: {badge['name']}")
    save_data(data)
    return user["badges"]

def update_streak(username: str):
    data = load_data()
    user = data["users"][username]
    today = datetime.now().date().isoformat()
    if user["lastActivityDate"] is None:
        user["currentStreak"] = 1
    elif user["lastActivityDate"] == today:
        pass
    else:
        last_date = datetime.fromisoformat(user["lastActivityDate"]).date()
        current_date = datetime.now().date()
        days_diff = (current_date - last_date).days
        if days_diff == 1:
            user["currentStreak"] += 1
            user["longestStreak"] = max(user["currentStreak"], user["longestStreak"])
        else:
            user["currentStreak"] = 1
    user["lastActivityDate"] = today
    save_data(data)

# ============================================
# UI PAGES
# ============================================

def page_login():
    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    st.markdown("""
    <div style="text-align:center;padding:40px 0 40px;">
        <h1 style="color:#1B4332;font-size:2.5em;margin:0;font-weight:700;">♻️ WasteWise</h1>
        <p style="color:#2D6A4F;font-size:1em;margin:10px 0 0;">Sort Waste. Earn Points. Save the Planet.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.show_register:
            st.markdown("<h3 style='text-align:center;color:#1B4332;'>Login to Your Account</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Login", use_container_width=True, key="login_btn"):
                    if username.strip():
                        success, result = login_user(username)
                        if success:
                            st.session_state.username = username
                            st.session_state.user_city = result["city"]
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                    else:
                        st.error("❌ Please enter a username")
            with col_b:
                if st.button("Sign Up", use_container_width=True, key="goto_register"):
                    st.session_state.show_register = True
                    st.rerun()
        else:
            st.markdown("<h3 style='text-align:center;color:#1B4332;'>Create Account</h3>", unsafe_allow_html=True)
            reg_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
            city = st.selectbox("City", ["Tempe, AZ", "Phoenix, AZ", "Mesa, AZ", "Scottsdale, AZ", "Other"], key="city_select")
            col_c, col_d = st.columns(2)
            with col_c:
                if st.button("Create Account", use_container_width=True, key="register_btn"):
                    if reg_username.strip():
                        success, message = register_user(reg_username, city)
                        if success:
                            st.session_state.username = reg_username
                            st.session_state.user_city = city
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Please enter a username")
            with col_d:
                if st.button("Back to Login", use_container_width=True, key="back_btn"):
                    st.session_state.show_register = False
                    st.rerun()


def page_dashboard():
    data = load_data()
    user = data["users"][st.session_state.username]

    st.markdown(f"""
    <div style="text-align:center;margin-bottom:24px;">
        <h1 style="color:#1B4332;font-size:2em;margin:0;">📊 Welcome Back, {st.session_state.username}</h1>
        <p style="color:#2D6A4F;font-size:0.95em;margin:6px 0 0;">📍 {st.session_state.user_city}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("⭐ Total Points", user['totalPoints'])
    with col2: st.metric("♻️ Items Sorted", user['totalItemsSorted'])
    with col3: st.metric("🔥 Current Streak", f"{user['currentStreak']} days")
    with col4: st.metric("🏆 Badges", len(user['badges']))

    st.markdown("---")
    st.markdown("<h2 style='color:#1B4332;text-align:center;'>🌍 Your Environmental Impact</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("🌍 CO₂ Avoided", f"{user['stats']['co2Saved']:.2f} kg")
    with col2: st.metric("💧 Water Saved", f"{user['stats']['waterSaved']:.1f} L")
    with col3: st.metric("🌳 Trees Saved", f"{user['stats']['treesSaved']:.3f}")

    if user["badges"]:
        st.markdown("---")
        st.markdown("<h2 style='color:#1B4332;text-align:center;'>🏆 Your Achievements</h2>", unsafe_allow_html=True)
        badge_cols = st.columns(min(len(user["badges"]), 6))
        for i, badge in enumerate(user["badges"]):
            with badge_cols[i % len(badge_cols)]:
                st.markdown(f"""
                <div style="background:#f0f7f4;padding:15px;border-radius:6px;text-align:center;border:1px solid #d4e8e0;">
                    <p style="font-size:2em;margin:0;">🎖️</p>
                    <p style="color:#1B4332;margin:8px 0 0;font-weight:600;font-size:0.9em;">{badge['name']}</p>
                </div>
                """, unsafe_allow_html=True)

    # Always show findings section — placeholder if empty
    st.markdown("---")
    st.markdown("<h2 style='color:#1B4332;text-align:center;'>📊 Your Sorting Findings</h2>", unsafe_allow_html=True)

    submissions = user.get("submissions", [])

    if not submissions:
        st.info("🌱 No classifications yet — go to **Sort** and scan your first item!")
        # Show sample chart so it doesn't look empty
        sample_df = pd.DataFrame({"Bin Type": ["Recycling", "Landfill", "Special", "Compost"], "Count": [0, 0, 0, 0]})
        fig = px.bar(sample_df, x="Bin Type", y="Count", color="Bin Type",
                     color_discrete_map={"Recycling": "#2D6A4F", "Compost": "#52B788", "Landfill": "#e74c3c", "Special": "#f59e0b"},
                     title="Your Waste Distribution (scan items to populate)")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            bin_counts = {}
            for sub in submissions:
                bt = sub.get("bin", "unknown")
                bin_counts[bt] = bin_counts.get(bt, 0) + 1
            bin_df = pd.DataFrame(list(bin_counts.items()), columns=["Bin Type", "Count"])
            fig = px.pie(bin_df, values="Count", names="Bin Type",
                         color_discrete_map={"recycling": "#2D6A4F", "compost": "#52B788", "landfill": "#e74c3c", "special": "#f59e0b"},
                         title="Your Waste Distribution")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            confidences = [sub.get("confidence", 0) for sub in submissions]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            verified = len([s for s in submissions if s.get("verified", False)])
            st.metric("📈 Avg Confidence", f"{avg_conf:.0%}")
            st.metric("✅ Verified Items", f"{verified}/{len(submissions)}")
            st.metric("📦 Total Classified", len(submissions))

        st.subheader("📝 Recent Classifications")
        for sub in sorted(submissions, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]:
            bin_emoji = {"recycling": "♻️", "compost": "🌱", "landfill": "🗑️", "special": "⚠️"}.get(sub.get("bin", ""), "📦")
            time_str = sub.get("timestamp", "").split("T")[0] if sub.get("timestamp") else "N/A"
            st.markdown(f"""
            <div style="background:#f0f7f4;padding:12px;border-radius:6px;margin:6px 0;border-left:3px solid #2D6A4F;">
                <strong style="color:#1B4332;">📦 {sub.get('item','Unknown')}</strong>
                <span style="color:#2D6A4F;margin-left:10px;">{bin_emoji} {sub.get('bin','unknown').title()}</span>
                <span style="float:right;color:#555;font-size:0.85em;">{sub.get('confidence',0):.0%} · {time_str}</span>
            </div>
            """, unsafe_allow_html=True)


def page_sort():
    st.markdown("# ♻️ Sort Your Waste")
    st.markdown("Take a photo or upload an image — Claude AI classifies it instantly and **auto-saves** your result.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📷 Take a Photo")
        captured_image = st.camera_input("Use your camera")
    with col2:
        st.subheader("📁 Upload Image")
        uploaded_image = st.file_uploader("Or upload from gallery", type=["jpg", "jpeg", "png", "webp"])

    image_data = captured_image if captured_image is not None else uploaded_image

    if image_data is not None:
        image = Image.open(image_data)
        st.image(image, caption="Waste item to classify", use_column_width=True)

        if st.button("🔍 Analyze Waste", use_container_width=True):
            with st.spinner("Claude AI is analyzing your item..."):
                image_bytes = image_data.getvalue()
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

                if hasattr(image_data, 'name'):
                    suffix = image_data.name.split('.')[-1].lower()
                    media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(suffix, "image/jpeg")
                else:
                    media_type = "image/jpeg"

                result = classify_waste(base64_image, st.session_state.user_city, media_type)

                if result:
                    # ── AUTO-SAVE immediately ──
                    item_key = result["item"] + result.get("bin", "")
                    if st.session_state.last_saved_item != item_key:
                        st.session_state.last_saved_item = item_key
                        auto_save_submission(result)
                        st.success(f"✅ Auto-saved! +{result['points']} points earned!")
                        st.balloons()

                    # ── Display result ──
                    bin_emoji = {"recycling": "♻️", "compost": "🌱", "landfill": "🗑️", "special": "⚠️"}.get(result["bin"], "")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("📦 Item", result['item'])
                    with col2: st.metric("🗑️ Bin", f"{bin_emoji} {result['bin'].title()}")
                    with col3: st.metric("🎯 Confidence", f"{result['confidence']*100:.0f}%")
                    with col4: st.metric("⭐ Points", f"+{result['points']}")

                    # Health impact lookup
                    HEALTH_IMPACT = {
                        "special": {
                            "icon": "🏥",
                            "title": "Human Health Risk — Handle with Care",
                            "color": "#7f1d1d",
                            "bg": "#fff1f2",
                            "border": "#f87171",
                            "message": "Improper disposal of this item leaches toxic chemicals into groundwater and soil. Communities near illegal dump sites show higher rates of respiratory disease, neurological disorders, and childhood developmental issues. Correct drop-off eliminates that risk."
                        },
                        "recycling": {
                            "icon": "💚",
                            "title": "Positive Health Impact",
                            "color": "#14532d",
                            "bg": "#f0fdf4",
                            "border": "#4ade80",
                            "message": "Recycling this item reduces industrial manufacturing demand, which cuts air pollution from factories. Studies show communities near recycling-active areas have lower rates of asthma and cardiovascular disease compared to landfill-heavy areas."
                        },
                        "landfill": {
                            "icon": "⚠️",
                            "title": "Landfill Health Concern",
                            "color": "#7c2d12",
                            "bg": "#fff7ed",
                            "border": "#fb923c",
                            "message": "Landfill decomposition produces methane and leachate that contaminate local air and water. Residents within 1 mile of landfills show elevated rates of low birth weight, preterm births, and respiratory illness. Only send here if no alternative exists."
                        },
                        "compost": {
                            "icon": "🌱",
                            "title": "Great for Community Health",
                            "color": "#14532d",
                            "bg": "#f0fdf4",
                            "border": "#4ade80",
                            "message": "Composting diverts organic waste from landfills, reducing methane — a greenhouse gas 80x more potent than CO₂ over 20 years. Compost-enriched soil grows healthier food with fewer pesticides, directly benefiting community nutrition."
                        }
                    }

                    health = HEALTH_IMPACT.get(result.get("bin", "landfill"), HEALTH_IMPACT["landfill"])

                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div style="background:#f0f7f4;padding:15px;border-radius:6px;border-left:3px solid #2D6A4F;margin-bottom:10px;">
                            <h4 style="color:#1B4332;margin-top:0;">💡 Why This Bin?</h4>
                            <p style="color:#444;margin:0;font-size:0.95em;">{result['reason']}</p>
                        </div>
                        <div style="background:#f0f7f4;padding:15px;border-radius:6px;border-left:3px solid #2D6A4F;">
                            <h4 style="color:#1B4332;margin-top:0;">🌍 Environmental Impact</h4>
                            <p style="color:#444;margin:0;font-size:0.95em;">{result['impact']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        st.markdown(f"""
                        <div style="background:#f0f7f4;padding:15px;border-radius:6px;border-left:3px solid #2D6A4F;margin-bottom:10px;">
                            <h4 style="color:#1B4332;margin-top:0;">📋 How to Prepare</h4>
                            <p style="color:#444;margin:0;font-size:0.95em;">{result['prep']}</p>
                        </div>
                        <div style="background:#f0f7f4;padding:15px;border-radius:6px;border-left:3px solid #2D6A4F;margin-bottom:10px;">
                            <h4 style="color:#1B4332;margin-top:0;">📊 Your Savings</h4>
                            <p style="color:#444;margin:4px 0;font-size:0.9em;">🌍 CO₂: -{result['environmentalImpact']['co2']:.2f}kg</p>
                            <p style="color:#444;margin:4px 0;font-size:0.9em;">💧 Water: -{result['environmentalImpact']['water']:.1f}L</p>
                            <p style="color:#444;margin:4px 0;font-size:0.9em;">🌳 Trees: +{result['environmentalImpact']['trees']:.4f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Health impact — full width below
                    st.markdown(f"""
                    <div style="background:{health['bg']};border:1px solid {health['border']};
                                border-left:4px solid {health['border']};
                                padding:16px 18px;border-radius:8px;margin-top:10px;">
                        <h4 style="color:{health['color']};margin:0 0 8px;">
                            {health['icon']} {health['title']}
                        </h4>
                        <p style="color:{health['color']};margin:0;font-size:0.92em;line-height:1.6;">
                            {health['message']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show drop-off map for special items
                    if result.get("bin") == "special":
                        show_dropoff_map(st.session_state.user_city)


def page_leaderboard():
    st.markdown("<h1 style='text-align:center;color:#1B4332;'>🏆 Community Leaderboard</h1>", unsafe_allow_html=True)
    data = load_data()
    cities = ["Global"] + list(set([u["city"] for u in data["users"].values()]))
    selected_city = st.selectbox("Filter by city", cities)

    if selected_city == "Global":
        leaderboard = sorted(data["leaderboard"], key=lambda x: x["totalPoints"], reverse=True)
    else:
        leaderboard = sorted([e for e in data["leaderboard"] if e["city"] == selected_city],
                             key=lambda x: x["totalPoints"], reverse=True)

    if not leaderboard:
        st.info("No users yet")
        return

    for rank, entry in enumerate(leaderboard[:20], 1):
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
        user = data["users"].get(entry["username"], {})
        submissions = user.get("submissions", [])
        confidences = [s.get("confidence", 0) for s in submissions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        bin_counts = {}
        for sub in submissions:
            bt = sub.get("bin", "unknown")
            bin_counts[bt] = bin_counts.get(bt, 0) + 1
        bin_display = "".join([
            f"<span style='margin-right:12px;'>{'♻️' if bt=='recycling' else '🌱' if bt=='compost' else '🗑️' if bt=='landfill' else '⚠️'} {cnt}</span>"
            for bt, cnt in sorted(bin_counts.items())
        ])
        st.markdown(f"""
        <div style="background:#ffffff;border:1px solid #d4e8e0;border-left:3px solid #2D6A4F;
                    padding:15px;border-radius:6px;margin:10px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:15px;">
                    <span style="font-size:1.8em;">{rank_emoji}</span>
                    <div>
                        <strong style="color:#1B4332;font-size:1.05em;">👤 {entry['username']}</strong><br>
                        <span style="color:#2D6A4F;font-size:0.9em;">📍 {entry['city']}</span><br>
                        <span style="font-size:0.85em;">{bin_display}</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <strong style="color:#2D6A4F;font-size:1.2em;">⭐ {entry['totalPoints']}</strong><br>
                    <span style="color:#555;font-size:0.85em;">♻️ {entry['totalItemsSorted']} items</span><br>
                    <span style="color:#555;font-size:0.85em;">🎯 {avg_confidence:.0%} confidence</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def page_profile():
    st.markdown(f"# 👤 Profile — {st.session_state.username}")
    data = load_data()
    user = data["users"][st.session_state.username]
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Statistics")
        st.write(f"**City:** {user['city']}")
        st.write(f"**Joined:** {user['joinedAt'][:10]}")
        st.write(f"**Total Points:** {user['totalPoints']}")
        st.write(f"**Items Sorted:** {user['totalItemsSorted']}")
        st.write(f"**Longest Streak:** {user['longestStreak']} days")
    with col2:
        st.subheader("🌍 Environmental Impact")
        st.write(f"**CO₂ Avoided:** {user['stats']['co2Saved']:.2f} kg")
        st.write(f"**Water Saved:** {user['stats']['waterSaved']:.1f} liters")
        st.write(f"**Trees Saved:** {user['stats']['treesSaved']:.3f}")
    if user["badges"]:
        st.subheader("🏆 Badges")
        cols = st.columns(len(user["badges"]))
        for i, badge in enumerate(user["badges"]):
            with cols[i]: st.info(badge["name"])
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.username = None
        st.session_state.user_city = None
        st.session_state.last_saved_item = None
        st.rerun()


def page_fiftyone_insights():
    st.markdown("""
    <div style='background:#1C4532;padding:1.5rem 2rem;border-radius:10px;
                margin-bottom:1.5rem;border:2px solid #52B788;'>
        <span style='color:#FFFFFF;font-size:1.8em;font-weight:700;
                     display:block;margin-bottom:0.4rem;'>🔬 Dataset Insights</span>
        <span style='color:#B7E4C7;font-size:1em;font-weight:500;display:block;'>
            Powered by FiftyOne — real-time AI performance tracking across all users
        </span>
    </div>
    """, unsafe_allow_html=True)

    df = get_analytics_data()

    if df.empty:
        st.info("No real submissions yet — showing sample data for demo.")
        items  = ["E-Waste Phone","Pizza Box","Battery","Plastic Bottle","Cardboard",
                  "Coffee Cup","Paint Can","Plastic Bag","Glass Jar","Newspaper"]
        bins   = ["special","recycling","special","recycling","recycling",
                  "landfill","special","landfill","recycling","recycling"]
        placeholder = []
        for i in range(30):
            idx = i % len(items)
            placeholder.append({
                "username": f"user{i%5}", "city": ["Tempe, AZ","Phoenix, AZ","Mesa, AZ"][i%3],
                "item": items[idx], "bin": bins[idx],
                "confidence": round(0.70 + (i % 20) * 0.01, 2),
                "timestamp": "2026-03-21T10:00:00", "verified": i % 4 == 0
            })
        df = pd.DataFrame(placeholder)

    total = len(df)
    avg_conf = df["confidence"].mean()
    recycling_rate = len(df[df["bin"] == "recycling"]) / total if total else 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("🔍 Total Scans", total)
    with col2: st.metric("🎯 Avg Confidence", f"{avg_conf:.0%}")
    with col3: st.metric("♻️ Recycling Rate", f"{recycling_rate:.0%}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Waste Distribution")
        bin_counts = df["bin"].value_counts()
        fig = px.bar(x=bin_counts.index.str.title(), y=bin_counts.values,
                     color=bin_counts.index.str.title(),
                     color_discrete_map={"Recycling":"#2D6A4F","Compost":"#52B788","Landfill":"#e74c3c","Special":"#f59e0b"},
                     labels={"x":"Bin Type","y":"Count"})
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(color="#1B4332", size=13),
            xaxis=dict(tickfont=dict(color="#1B4332", size=12),
                       title_font=dict(color="#1B4332", size=13)),
            yaxis=dict(tickfont=dict(color="#1B4332", size=12),
                       title_font=dict(color="#1B4332", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True, key="fo_bar")
    with col2:
        st.subheader("Confidence Distribution")
        fig = px.histogram(df, x="confidence", nbins=15,
                           color_discrete_sequence=["#2D6A4F"],
                           labels={"confidence":"Confidence Score","count":"Count"})
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(color="#1B4332", size=13),
            xaxis=dict(tickfont=dict(color="#1B4332", size=12),
                       title_font=dict(color="#1B4332", size=13)),
            yaxis=dict(tickfont=dict(color="#1B4332", size=12),
                       title_font=dict(color="#1B4332", size=13)),
        )
        st.plotly_chart(fig, use_container_width=True, key="fo_hist")

    st.markdown("""
    <div style='background:#f0f7f4;border:1px solid #d4e8e0;border-left:4px solid #2D6A4F;
                padding:14px 18px;border-radius:6px;margin-top:1rem;'>
        <h4 style='color:#1B4332;margin:0 0 6px;'>🔬 How FiftyOne Powers This</h4>
        <p style='color:#444;margin:0;font-size:0.9em;'>
            Every photo classified is stored as a <strong>FiftyOne sample</strong> with labels,
            confidence scores, and metadata. This lets us visually inspect failures,
            find edge cases (greasy vs clean cardboard), and build a ground-truth dataset
            that improves over time. This is what separates WasteWise from a chatbot wrapper —
            it's a <strong>data pipeline</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    low_conf = df[df["confidence"] < 0.75]
    if len(low_conf) > 0:
        st.markdown("---")
        st.subheader("⚠️ Ambiguous Items (confidence < 75%) — candidates for review")
        display = low_conf[["item","bin","confidence","city"]].copy()
        display.columns = ["Item","Bin","Confidence","City"]
        display["Confidence"] = display["Confidence"].apply(lambda x: f"{x:.0%}")
        st.dataframe(display.head(10), use_container_width=True)


def page_insights():
    st.markdown("# 📈 City Insights & Trends")
    data = load_data()
    cities = sorted(set([u["city"] for u in data["users"].values()]))
    if not cities:
        st.info("No data yet. Classify some items first!")
        return
    selected_city = st.selectbox("Select City", cities)
    if selected_city:
        stats = get_city_statistics(selected_city)
        if stats is None:
            st.info("No data yet for this city")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📊 Total Items", stats["total_submissions"])
            with col2: st.metric("♻️ Recycling %", f"{stats['recycling_count']/stats['total_submissions']*100:.0f}%")
            with col3: st.metric("🌱 Compost %", f"{stats['compost_count']/stats['total_submissions']*100:.0f}%")
            with col4: st.metric("✅ Verified Rate", f"{stats['verified_rate']:.0f}%")
            waste_df = pd.DataFrame(list({"Recycling": stats["recycling_count"], "Compost": stats["compost_count"],
                                          "Landfill": stats["landfill_count"], "Special": stats["special_count"]}.items()),
                                    columns=["Bin Type", "Count"])
            fig = px.pie(waste_df, values="Count", names="Bin Type",
                         color_discrete_map={"Recycling":"#2ecc71","Compost":"#27ae60","Landfill":"#e74c3c","Special":"#f39c12"})
            st.plotly_chart(fig, use_container_width=True)


def page_research_dashboard():
    st.markdown("# 📋 Research Dashboard")
    df = get_analytics_data()

    if df.empty:
        st.info("No real data yet — showing sample data.")
        items  = ["E-Waste Phone","Pizza Box","Battery","Plastic Bottle","Cardboard",
                  "Coffee Cup","Paint Can","Plastic Bag","Glass Jar","Newspaper"]
        bins   = ["special","recycling","special","recycling","recycling",
                  "landfill","special","landfill","recycling","recycling"]
        placeholder = []
        for i in range(40):
            idx = i % len(items)
            placeholder.append({
                "username": f"user{i%6}", "city": ["Tempe, AZ","Phoenix, AZ","Mesa, AZ"][i%3],
                "item": items[idx], "bin": bins[idx],
                "confidence": round(0.65 + (i % 30) * 0.01, 2),
                "timestamp": "2026-03-21T10:00:00", "verified": i % 3 == 0
            })
        df = pd.DataFrame(placeholder)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Submissions", len(df))
    with col2: st.metric("Unique Users", df['username'].nunique())
    with col3: st.metric("Cities", df['city'].nunique())
    with col4: st.metric("Avg Confidence", f"{df['confidence'].mean():.1%}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        bin_counts = df['bin'].value_counts()
        fig = px.pie(values=bin_counts.values, names=bin_counts.index, title="By Waste Type",
                     color_discrete_map={"recycling":"#2ecc71","compost":"#27ae60","landfill":"#e74c3c","special":"#f39c12"})
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(df, x='confidence', nbins=20, title="Confidence Distribution",
                           color_discrete_sequence=["#2D6A4F"])
        st.plotly_chart(fig, use_container_width=True)

    item_counts = df['item'].value_counts().head(10)
    fig = px.bar(x=item_counts.values, y=item_counts.index, orientation='h',
                 title="Top Waste Items", color=item_counts.values, color_continuous_scale="Greens")
    st.plotly_chart(fig, use_container_width=True)


def page_admin_analytics():
    st.markdown("# 📊 Admin Analytics")
    admin_password = st.text_input("Admin Password", type="password")
    if admin_password != "admin123":
        st.error("Unauthorized")
        return
    st.success("✅ Admin Access Granted")
    df = get_analytics_data()
    if df.empty:
        st.info("No submissions yet")
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Submissions", len(df))
    with col2: st.metric("Unique Users", df['username'].nunique())
    with col3: st.metric("Cities", df['city'].nunique())
    with col4: st.metric("Verified", len(df[df['verified'] == True]))
    fig = px.pie(values=df['bin'].value_counts().values, names=df['bin'].value_counts().index, title="By Bin Type")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.sort_values('timestamp', ascending=False).head(20), use_container_width=True)


# ============================================
# MAIN APP
# ============================================

def main():
    init_user_session()

    if st.session_state.username is None:
        page_login()
    else:
        st.sidebar.markdown(f"**👤 {st.session_state.username}**")
        st.sidebar.markdown(f"📍 {st.session_state.user_city}")
        st.sidebar.divider()

        is_admin = st.sidebar.checkbox("🔐 Admin Mode")

        if is_admin:
            page = st.sidebar.radio("Admin Tools",
                ["Dashboard", "Sort", "Leaderboard", "🔬 Dataset Insights",
                 "📊 Analytics", "📋 Research Dashboard", "Profile"])
        else:
            page = st.sidebar.radio("Navigate",
                ["Dashboard", "Sort", "Leaderboard", "🔬 Dataset Insights",
                 "📈 City Insights", "Profile"])

        if page == "Dashboard":           page_dashboard()
        elif page == "Sort":              page_sort()
        elif page == "Leaderboard":       page_leaderboard()
        elif page == "🔬 Dataset Insights": page_fiftyone_insights()
        elif page == "📈 City Insights":  page_insights()
        elif page == "Profile":           page_profile()
        elif page == "📊 Analytics":      page_admin_analytics()
        elif page == "📋 Research Dashboard": page_research_dashboard()

if __name__ == "__main__":
    main()
