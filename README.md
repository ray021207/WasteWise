# ♻️ WasteWise
### AI-Powered Waste Disposal Intelligence — Built with Claude Sonnet + FiftyOne

> *Every year, $1.5 billion worth of recyclables go to landfill — not because people don't care, but because the rules are confusing and change by ZIP code. WasteWise fixes that.*

Built at the **Agents World: Visual AI Hackathon @ ASU** (March 2026) — Voxel51 × Anthropic

---

## 🌍 The Problem

- **25%** of recyclables are contaminated at source — one greasy pizza box ruins an entire batch
- **62%** of Americans are confused about what goes where
- Disposal rules vary by city, neighborhood, and hauler — Google gives generic answers
- Nobody has built a reasoning layer on top of that complexity — until now

---

## 💡 What WasteWise Does

Snap a photo of any item → Claude Sonnet 4.6 **reasons** about it (not just classifies) → get hyperlocal disposal guidance for your exact city, instantly.

Unlike lookup tables, Claude handles edge cases:
- *"Is this pizza box recyclable?"* — depends if it's greasy
- *"What about this plastic bag?"* — store drop-off, NOT curbside
- *"Old smartphone?"* — special e-waste, here are the 3 nearest drop-off locations

**FiftyOne** powers the data layer — every classification is stored as a labeled sample, letting us visualize where the AI succeeds, find failure modes, and build a ground-truth dataset that improves over time.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📸 **Live Camera + Upload** | Snap a photo on your phone or upload from gallery |
| 🤖 **Claude Sonnet 4.6 Vision** | Reasoning-based classification, not just pattern matching |
| 📍 **Hyperlocal Rules** | City-specific disposal logic (Phoenix ≠ Seattle ≠ NYC) |
| 🗺️ **Drop-off Map** | Nearest special disposal locations for hazardous items |
| 🔬 **FiftyOne Analytics** | Real-time AI performance tracking across all users |
| 🌍 **Impact Tracking** | CO₂ avoided, water saved, trees saved per item |
| 🏆 **Leaderboard + Badges** | Community competition to drive behavior change |
| 📊 **Research Dashboard** | City-wide waste trends and classification data export |

---

## 🚀 Quick Start

### 1. Install
```bash
pip install -r requirements_streamlit.txt
```

### 2. Configure
```bash
cp .env.example .env
# Add your Anthropic API key from https://console.anthropic.com
```

### 3. Run
```bash
streamlit run wastewise_streamlit.py
```
Opens at `http://localhost:8501`

---

## 📱 Run on Your Phone (Best for Demo)

```bash
streamlit run wastewise_streamlit.py --server.address 0.0.0.0
```

Find your computer's IP (`ipconfig` on Windows, `ifconfig` on Mac/Linux) then open `http://YOUR-IP:8501` on your phone. Camera works natively.

---

## ☁️ Deploy to Streamlit Cloud (Free, Permanent URL)

```bash
git add .
git commit -m "deploy"
git push origin main
```

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Main file: `wastewise_streamlit.py`
4. Add `ANTHROPIC_API_KEY` to Secrets
5. Share the live URL with anyone, anywhere

---

## 🔬 FiftyOne Integration

Every classification is logged to a FiftyOne dataset with:
- Image sample + filepath
- Predicted bin type (recycling / compost / landfill / special)
- Claude's confidence score
- City, username, timestamp
- Human verification status (admin QC)

This creates a **continuously improving ground-truth dataset** — the foundation for training a specialized waste classification model.

**Admin access:** Check `🔐 Admin Mode` in sidebar → password `admin123`

---

## 🏆 Gamification

| Bin Type | Points |
|----------|--------|
| ♻️ Recycling | 100 × confidence |
| 🌱 Compost | 120 × confidence |
| ⚠️ Special/Hazmat | 150 × confidence |
| 🗑️ Landfill | 25 × confidence |

**Badges:** First Step → Quick Starter → Eco Warrior → Legendary Sorter → 7-Day Streak → 30-Day Legend

---

## 🗺️ Real-World Impact

A 30% reduction in contamination saves a mid-size city like Phoenix **$500K+/year** in landfill diversion fees. WasteWise attacks the root cause — behavior at the point of disposal — with AI reasoning that actually explains *why*, so users learn over time.

---

## 🛣️ Roadmap

- [ ] **Google Places API** — real drop-off locations for any address worldwide
- [ ] **50 US cities** — expand beyond Phoenix metro
- [ ] **Municipal API integrations** — live rule updates from city databases
- [ ] **Bilingual support** — Spanish-first for broader community reach
- [ ] **City government dashboard** — sell insights to sustainability offices
- [ ] **FiftyOne plugin** — open-source waste classification operator

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Vision + Reasoning | Claude Sonnet 4.6 (Anthropic) |
| Dataset Management | FiftyOne (Voxel51) |
| Frontend | Streamlit |
| Data Storage | JSON → upgradeable to PostgreSQL |
| Deployment | Streamlit Cloud |

---

## 📁 Project Structure

```
wastewise_streamlit.py    ← Entire app (single file)
requirements_streamlit.txt
wastewise_data.json       ← Auto-created on first run
.env                      ← Your API key (create from .env.example)
.env.example
```

---

## 💰 API Cost

- Per image analysis: ~$0.003
- 100 users × 20 images/month: ~$6.00
- Free tier at [console.anthropic.com](https://console.anthropic.com) covers development

---

## 👤 Built By

**Ray** — ASU Student  
Built solo in 24 hours at Agents World: Visual AI Hackathon @ ASU  
*Wildcard Track — Sustainability*

---

*"Every correctly sorted item is a small act of impact."*
