# -*- coding: utf-8 -*-
import streamlit as st
import json
import os
from dotenv import load_dotenv
from groq import Groq
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="EduPath - AI Enquiry Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def inject_css():
    with open("style.css", "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_css()

# ─────────────────────────────────────────────
# Init
# ─────────────────────────────────────────────
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

with open("courses.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

COURSE_NAMES = [c["name"] for c in courses]

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
for key, default in {
    "messages":    [],
    "lead_stage":  "none",   # none | collecting | done
    "last_lead":   {},       # stores last captured lead for preview
    "pending":     None,
    "language":    "English",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────
# System Prompts (English + Malayalam)
# ─────────────────────────────────────────────
COURSE_CONTEXT = json.dumps(courses, indent=2)

SYSTEM_PROMPTS = {
    "English": f"""You are EduPath AI, a friendly and concise enquiry assistant for a training academy.

COURSES:
{COURSE_CONTEXT}

RULES:
1. Answer questions about courses, fees, duration, placements, and batch dates clearly.
2. If the student wants to join/enroll/register — reply enthusiastically and end with exactly: [COLLECT_LEAD]
3. If asked to COMPARE courses (e.g. "compare X and Y") — end your reply with exactly: [SHOW_COMPARISON:CourseName1|CourseName2]
4. For recommendations, ask ONE question about their goal, then suggest the best match.
5. Keep responses under 4 sentences unless listing details.
6. Never invent information not in the course data.
7. Always respond in English.
""",

    "Malayalam": f"""നിങ്ങൾ EduPath AI ആണ്, ഒരു ട്രെയിനിംഗ് അക്കാദമിയുടെ സഹായകരമായ enquiry assistant.

കോഴ്സുകൾ:
{COURSE_CONTEXT}

നിയമങ്ങൾ:
1. കോഴ്സുകൾ, ഫീസ്, ദൈർഘ്യം, placement, batch തീയതികൾ എന്നിവ വ്യക്തമായി ഉത്തരം നൽകുക.
2. വിദ്യാർത്ഥി join/enroll/register ചെയ്യാൻ ആഗ്രഹിക്കുന്നുവെങ്കിൽ — ഉത്സാഹത്തോടെ മറുപടി നൽകി ഇങ്ങനെ അവസാനിക്കുക: [COLLECT_LEAD]
3. കോഴ്സുകൾ compare ചെയ്യാൻ ആവശ്യപ്പെട്ടാൽ — ഇങ്ങനെ അവസാനിക്കുക: [SHOW_COMPARISON:CourseName1|CourseName2]
4. ശുപാർശകൾക്ക്, അവരുടെ ലക്ഷ്യത്തെക്കുറിച്ച് ഒരു ചോദ്യം ചോദിക്കുക, പിന്നെ ഏറ്റവും നല്ല കോഴ്സ് നിർദ്ദേശിക്കുക.
5. വിവരങ്ങൾ ലിസ്റ്റ് ചെയ്യുന്നതൊഴികെ 4 വാക്യങ്ങളിൽ കൂടരുത്.
6. കോഴ്സ് ഡാറ്റയിൽ ഇല്ലാത്ത വിവരങ്ങൾ കണ്ടുപിടിക്കരുത്.
7. എല്ലായ്പ്പോഴും മലയാളത്തിൽ മാത്രം മറുപടി നൽകുക.
""",
}

WELCOME_MESSAGES = {
    "English": "👋 Hi! I'm your <strong>EduPath AI Assistant</strong>.<br><br>I can help you with course details, fees, placements, and enrollment. What would you like to know?",
    "Malayalam": "👋 നമസ്കാരം! ഞാൻ നിങ്ങളുടെ <strong>EduPath AI Assistant</strong> ആണ്.<br><br>കോഴ്സ് വിവരങ്ങൾ, ഫീസ്, placement, enrollment എന്നിവയിൽ സഹായിക്കാൻ ഞാൻ ഇവിടെ ഉണ്ട്. എന്ത് അറിയണം?",
}

STARTER_CHIPS = {
    "English": ["What courses do you offer?", "Python course fee?", "Do you have placements?", "Suggest a course for me", "Compare Data Science vs Python Full Stack"],
    "Malayalam": ["എന്ത് കോഴ്സുകൾ ഉണ്ട്?", "Python കോഴ്സ് ഫീസ് എത്ര?", "Placement ഉണ്ടോ?", "എനിക്ക് ഒരു കോഴ്സ് നിർദ്ദേശിക്കൂ", "Data Science vs Python Full Stack താരതമ്യം"],
}

FORM_LABELS = {
    "English": {"name": "Your Name *", "phone": "WhatsApp Number *", "email": "Email Address", "course": "Interested Course", "submit": "Submit Enquiry", "name_ph": "e.g. Arjun Nair", "phone_ph": "e.g. 9876543210", "email_ph": "you@email.com"},
    "Malayalam": {"name": "നിങ്ങളുടെ പേര് *", "phone": "WhatsApp നമ്പർ *", "email": "ഇമെയിൽ വിലാസം", "course": "താൽപ്പര്യമുള്ള കോഴ്സ്", "submit": "Enquiry സമർപ്പിക്കുക", "name_ph": "ഉദാ: അർജുൻ നായർ", "phone_ph": "ഉദാ: 9876543210", "email_ph": "you@email.com"},
}

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def get_ai_response(user_msg: str) -> str:
    lang = st.session_state.language
    history = [{"role": "system", "content": SYSTEM_PROMPTS[lang]}]
    for m in st.session_state.messages[-10:]:
        history.append({"role": m["role"], "content": m["content"]})
    history.append({"role": "user", "content": user_msg})
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=history,
        temperature=0.7,
        max_tokens=400,
    )
    return resp.choices[0].message.content


def score_lead() -> str:
    text = " ".join(m["content"] for m in st.session_state.messages if m["role"] == "user").lower()
    kws  = ["join","enroll","register","fee","placement","batch","start","admission","cost","price"]
    hits = sum(1 for k in kws if k in text)
    if "join" in text or "enroll" in text or hits >= 3:
        return "hot"
    if hits >= 1 or len(st.session_state.messages) >= 4:
        return "warm"
    return "cold"


def save_lead(name, phone, email, course):
    row = {"Name": name, "Phone": phone, "Email": email, "Course": course,
           "Score": score_lead(), "Language": st.session_state.language,
           "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    new_df = pd.DataFrame([row])
    try:
        old_df = pd.read_csv("leads.csv")
        if "Score" in old_df.columns:
            old_df["Score"] = old_df["Score"].fillna("cold").replace("nan","cold")
        else:
            old_df["Score"] = "cold"
        if "Language" not in old_df.columns:
            old_df["Language"] = "English"
        final = pd.concat([old_df, new_df], ignore_index=True)
    except Exception:
        final = new_df
    final.to_csv("leads.csv", index=False)
    return row


def load_leads() -> pd.DataFrame:
    try:
        df = pd.read_csv("leads.csv")
        if "Score" in df.columns:
            df["Score"] = df["Score"].fillna("cold").astype(str)
            df["Score"] = df["Score"].apply(lambda x: "cold" if x.lower() in ["nan","none",""] else x.lower())
        else:
            df["Score"] = "cold"
        if "Language" not in df.columns:
            df["Language"] = "English"
        return df
    except Exception:
        return pd.DataFrame(columns=["Name","Phone","Email","Course","Score","Language","Time"])


def add_msg(role: str, text: str):
    st.session_state.messages.append({"role": role, "content": text, "time": datetime.now().strftime("%H:%M")})


def render_bubble(msg: dict):
    is_bot  = msg["role"] == "assistant"
    content = msg["content"].replace("\n", "<br>")
    t       = msg.get("time", "")
    row_cls = "" if is_bot else " user"
    av_cls  = "bot" if is_bot else "user"
    b_cls   = "bot" if is_bot else "user"
    icon    = "&#127891;" if is_bot else "&#128100;"
    time_cls = "msg-time" if is_bot else "msg-time r"
    st.markdown(f"""
    <div class="msg-row{row_cls}">
      <div class="msg-av {av_cls}">{icon}</div>
      <div style="max-width:75%">
        <div class="bubble {b_cls}">{content}</div>
        <div class="{time_cls}">{t}</div>
      </div>
    </div>""", unsafe_allow_html=True)


def get_course_by_name(name: str):
    for c in courses:
        if c["name"].lower() == name.lower():
            return c
    # fuzzy
    for c in courses:
        if name.lower() in c["name"].lower() or c["name"].lower() in name.lower():
            return c
    return None


def render_comparison(c1_name: str, c2_name: str):
    c1 = get_course_by_name(c1_name)
    c2 = get_course_by_name(c2_name)
    if not c1 or not c2:
        return
    fields = ["name","duration","fees","placement","next_batch","eligibility"]
    labels = ["Course","Duration","Fees","Placement","Next Batch","Eligibility"]
    rows = ""
    for field, label in zip(fields, labels):
        v1 = c1.get(field, "—")
        v2 = c2.get(field, "—")
        rows += f'<tr><td class="field-label">{label}</td><td>{v1}</td><td>{v2}</td></tr>'
    st.markdown(f"""
    <div class="compare-wrap">
      <div class="compare-title">&#128202; Course Comparison</div>
      <table class="compare-table">
        <thead><tr><th>Feature</th><th>{c1.get('name','')}</th><th>{c2.get('name','')}</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)


def render_followup_preview(lead: dict):
    name   = lead.get("Name", "Student")
    course = lead.get("Course", "the course")
    phone  = lead.get("Phone", "")
    email  = lead.get("Email", "")
    now    = datetime.now().strftime("%H:%M")
    today  = datetime.now().strftime("%B %d, %Y")

    wa_msg = (
        f"Hello {name}! 👋\n\n"
        f"Thank you for your interest in *{course}* at EduPath Academy.\n\n"
        f"Our counsellor will call you within *2 hours* to guide you through the enrollment process.\n\n"
        f"📅 Next batch starts soon — reserve your seat!\n\n"
        f"_EduPath Academy — Learn. Grow. Succeed._"
    ).replace("\n", "<br>")

    email_body = (
        f"Dear {name},<br><br>"
        f"Thank you for enquiring about our <strong>{course}</strong> program.<br><br>"
        f"We have received your details and our academic counsellor will reach out to you at <strong>{phone}</strong> "
        f"within the next 2 business hours.<br><br>"
        f"In the meantime, feel free to explore our course brochure attached below.<br><br>"
        f"Warm regards,<br><strong>EduPath Academy Team</strong>"
    )

    st.markdown("""<div class="followup-section"><div class="followup-title">&#128228; Automated Follow-up Preview</div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="wa-preview">
          <div class="wa-preview-header">
            <div class="wa-preview-icon">&#128240;</div>
            <div>
              <div class="wa-preview-label">WhatsApp Message</div>
              <div style="font-size:0.65rem;color:#64748b">EduPath Academy → {name}</div>
            </div>
            <div class="wa-preview-time">{now}</div>
          </div>
          {wa_msg}
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="email-preview">
          <div class="email-preview-header">
            <div class="email-icon">&#9993;</div>
            <div>
              <div class="email-label">Email Notification</div>
              <div style="font-size:0.65rem;color:#64748b">admissions@edupath.in → {email or 'student'}</div>
            </div>
          </div>
          <div class="email-field">To: <span>{email or '(no email provided)'}</span></div>
          <div class="email-field">Subject: <span>Your Enquiry for {course} — EduPath Academy</span></div>
          <div class="email-field">Date: <span>{today}</span></div>
          <br>{email_body}
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Process pending message BEFORE render
# ─────────────────────────────────────────────
comparison_pending = None

if st.session_state.pending:
    user_msg = st.session_state.pending
    st.session_state.pending = None
    add_msg("user", user_msg)
    raw = get_ai_response(user_msg)

    # Check triggers
    trigger_lead    = "[COLLECT_LEAD]" in raw
    trigger_compare = "[SHOW_COMPARISON:" in raw

    # Extract comparison courses
    if trigger_compare:
        try:
            part = raw.split("[SHOW_COMPARISON:")[1].split("]")[0]
            c1_name, c2_name = part.split("|")
            st.session_state["_compare"] = (c1_name.strip(), c2_name.strip())
        except Exception:
            pass

    clean = raw
    for tag in ["[COLLECT_LEAD]"]:
        clean = clean.replace(tag, "")
    if "[SHOW_COMPARISON:" in clean:
        clean = clean[:clean.index("[SHOW_COMPARISON:")]

    add_msg("assistant", clean.strip())

    if trigger_lead and st.session_state.lead_stage == "none":
        st.session_state.lead_stage = "collecting"

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_chat, tab_admin = st.tabs(["💬  Chat Assistant", "📊  Admin Dashboard"])

# ═══════════════════════════════════════════════
# TAB 1 — CHAT
# ═══════════════════════════════════════════════
with tab_chat:
    left, main = st.columns([1, 2.8], gap="large")

    # ── LEFT: Courses + Language Toggle ──
    with left:
        st.markdown("""
        <div class="brand-strip">
          <div class="brand-icon">&#127891;</div>
          <div>
            <div class="brand-name">EduPath</div>
            <div class="brand-tag">AI Assistant</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Language toggle
        st.markdown("<div class='sec-label'>Language / ഭാഷ</div>", unsafe_allow_html=True)
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            if st.button("🇬🇧 English",
                         key="lang_en",
                         use_container_width=True,
                         type="primary" if st.session_state.language == "English" else "secondary"):
                st.session_state.language  = "English"
                st.session_state.messages  = []
                st.session_state.lead_stage = "none"
                st.rerun()
        with lang_col2:
            if st.button("🇮🇳 മലയാളം",
                         key="lang_ml",
                         use_container_width=True,
                         type="primary" if st.session_state.language == "Malayalam" else "secondary"):
                st.session_state.language  = "Malayalam"
                st.session_state.messages  = []
                st.session_state.lead_stage = "none"
                st.rerun()

        st.markdown("<br><div class='sec-label'>Our Courses</div>", unsafe_allow_html=True)

        for c in courses:
            st.markdown(f"""
            <div class="course-card">
              <div class="course-card-name">{c['name']}</div>
              <div class="course-card-meta">
                <span>&#9202; {c['duration']}</span>
                <span class="course-card-fee">{c['fees']}</span>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""<br>
        <div style="font-size:0.78rem;color:#94a3b8;">
          <span class="status-dot"></span>AI Online &middot; Groq LLaMA 3.1
        </div>""", unsafe_allow_html=True)

    # ── MAIN: Chat ──
    with main:
        lang = st.session_state.language
        subtitle = "Powered by Groq · LLaMA 3.1 · Instant AI responses" if lang == "English" else "Groq · LLaMA 3.1 · തൽക്ഷണ AI മറുപടി"

        st.markdown(f"""
        <div class="chat-header">
          <div class="chat-avatar">&#129302;</div>
          <div>
            <div class="chat-title">EduPath Enquiry Assistant</div>
            <div class="chat-subtitle">{subtitle}</div>
          </div>
          <div style="margin-left:auto;background:#eff6ff;border:1px solid #bfdbfe;
               border-radius:20px;padding:4px 12px;font-size:0.75rem;
               font-weight:600;color:#1e40af;">
            {'🇬🇧 English' if lang == 'English' else '🇮🇳 Malayalam'}
          </div>
        </div>""", unsafe_allow_html=True)

        # Welcome
        if not st.session_state.messages:
            st.markdown(f"""
            <div class="msg-row">
              <div class="msg-av bot">&#127891;</div>
              <div>
                <div class="bubble bot">{WELCOME_MESSAGES[lang]}</div>
              </div>
            </div>""", unsafe_allow_html=True)

            chips = STARTER_CHIPS[lang]
            cols  = st.columns(len(chips))
            for i, label in enumerate(chips):
                with cols[i]:
                    if st.button(label, key=f"chip_{i}", use_container_width=True):
                        st.session_state.pending = label
                        st.rerun()

        # Render messages
        for msg in st.session_state.messages:
            render_bubble(msg)

        # Comparison table (rendered after last message)
        if "_compare" in st.session_state:
            c1_name, c2_name = st.session_state.pop("_compare")
            render_comparison(c1_name, c2_name)

        # Lead form
        if st.session_state.lead_stage == "collecting":
            lbl = FORM_LABELS[lang]
            st.markdown("""
            <div class="lead-card">
              <div class="lead-card-title">&#10024; Great! Fill in your details to get enrolled</div>
            </div>""", unsafe_allow_html=True)

            with st.form("lead_form", clear_on_submit=False):
                c1, c2 = st.columns(2)
                with c1:
                    name  = st.text_input(lbl["name"],  placeholder=lbl["name_ph"])
                with c2:
                    phone = st.text_input(lbl["phone"], placeholder=lbl["phone_ph"])
                email  = st.text_input(lbl["email"],  placeholder=lbl["email_ph"])
                course = st.selectbox(lbl["course"],  COURSE_NAMES)
                submitted = st.form_submit_button(lbl["submit"], use_container_width=True)

                if submitted:
                    errors = []
                    is_en  = lang == "English"

                    # ── Name validation ──
                    name_clean = name.strip()
                    if not name_clean:
                        errors.append("⚠️ Name is required." if is_en else "⚠️ പേര് നൽകുക.")
                    elif len(name_clean) < 2:
                        errors.append("⚠️ Name must be at least 2 characters." if is_en else "⚠️ പേര് കുറഞ്ഞത് 2 അക്ഷരം ഉണ്ടായിരിക്കണം.")
                    elif not all(c.isalpha() or c.isspace() for c in name_clean):
                        errors.append("⚠️ Name should contain only letters." if is_en else "⚠️ പേരിൽ അക്ഷരങ്ങൾ മാത്രം ഉപയോഗിക്കുക.")

                    # ── Phone validation ──
                    phone_clean = phone.strip().replace(" ", "").replace("-", "")
                    if not phone_clean:
                        errors.append("⚠️ Phone number is required." if is_en else "⚠️ ഫോൺ നമ്പർ നൽകുക.")
                    elif not phone_clean.lstrip("+").isdigit():
                        errors.append("⚠️ Phone number must contain only digits." if is_en else "⚠️ ഫോൺ നമ്പർ അക്കങ്ങൾ മാത്രം ആകണം.")
                    elif len(phone_clean.lstrip("+")) < 10:
                        errors.append("⚠️ Enter a valid 10-digit phone number." if is_en else "⚠️ 10 അക്കമുള്ള ഫോൺ നമ്പർ നൽകുക.")
                    elif len(phone_clean.lstrip("+")) > 13:
                        errors.append("⚠️ Phone number is too long." if is_en else "⚠️ ഫോൺ നമ്പർ വളരെ നീളമുണ്ട്.")

                    # ── Email validation (if provided) ──
                    email_clean = email.strip()
                    if email_clean:
                        import re
                        email_pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
                        if not re.match(email_pattern, email_clean):
                            errors.append("⚠️ Please enter a valid email address." if is_en else "⚠️ ശരിയായ ഇമെയിൽ വിലാസം നൽകുക.")

                    # ── Duplicate phone check ──
                    if not errors:
                        try:
                            existing = pd.read_csv("leads.csv")
                            existing_phones = existing["Phone"].astype(str).str.replace(r"\D","",regex=True).tolist()
                            if phone_clean.lstrip("+") in existing_phones:
                                errors.append("⚠️ This phone number has already been registered." if is_en else "⚠️ ഈ ഫോൺ നമ്പർ ഇതിനകം രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്.")
                        except Exception:
                            pass

                    # ── Show errors or save ──
                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        lead = save_lead(name_clean, phone_clean, email_clean, course)
                        st.session_state.lead_stage = "done"
                        st.session_state.last_lead  = lead
                        if is_en:
                            confirm = (f"Thank you, {name_clean}! Your enquiry for {course} has been saved. "
                                       f"Our counsellor will call you at {phone_clean} within 2 hours. "
                                       "Feel free to ask anything else!")
                        else:
                            confirm = (f"നന്ദി, {name_clean}! {course} കോഴ്സിനായുള്ള നിങ്ങളുടെ enquiry സേവ് ചെയ്തു. "
                                       f"ഞങ്ങളുടെ counsellor 2 മണിക്കൂറിനുള്ളിൽ {phone_clean} ൽ വിളിക്കും. "
                                       "മറ്റെന്തെങ്കിലും ചോദ്യങ്ങൾ ഉണ്ടോ?")
                        add_msg("assistant", confirm)
                        st.rerun()

        # Follow-up preview (shown after lead captured)
        if st.session_state.lead_stage == "done" and st.session_state.last_lead:
            render_followup_preview(st.session_state.last_lead)

        # Chat input
        st.markdown("<br>", unsafe_allow_html=True)
        placeholder = "Ask anything about our courses..." if lang == "English" else "കോഴ്സുകളെക്കുറിച്ച് എന്തും ചോദിക്കൂ..."
        with st.form("chat_input", clear_on_submit=True):
            col_msg, col_btn = st.columns([5, 1])
            with col_msg:
                user_text = st.text_input("", placeholder=placeholder, label_visibility="collapsed")
            with col_btn:
                send = st.form_submit_button("Send ➤", use_container_width=True)

        if send and user_text.strip():
            st.session_state.pending = user_text.strip()
            st.rerun()

# ═══════════════════════════════════════════════
# TAB 2 — ADMIN DASHBOARD
# ═══════════════════════════════════════════════
with tab_admin:
    leads_df = load_leads()
    total = len(leads_df)
    hot   = int((leads_df["Score"] == "hot").sum())
    warm  = int((leads_df["Score"] == "warm").sum())
    cold  = int((leads_df["Score"] == "cold").sum())

    st.markdown("### 📊 Admin Dashboard")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stat Cards ──
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#1e40af">{total}</div><div class="stat-lbl">Total Leads</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#dc2626">{hot}</div><div class="stat-lbl">Hot &#128293;</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#ea580c">{warm}</div><div class="stat-lbl">Warm &#9832;</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="stat-card"><div class="stat-num" style="color:#2563eb">{cold}</div><div class="stat-lbl">Cold &#10052;</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if total == 0:
        st.info("No leads captured yet. Start a conversation in the Chat tab!")
    else:
        # ── 1. Full Table (top) ──
        st.markdown("#### All Enquiries")
        st.dataframe(
            leads_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Name":     st.column_config.TextColumn("Name",     width="medium"),
                "Phone":    st.column_config.TextColumn("Phone",    width="medium"),
                "Email":    st.column_config.TextColumn("Email",    width="large"),
                "Course":   st.column_config.TextColumn("Course",   width="large"),
                "Score":    st.column_config.TextColumn("Score",    width="small"),
                "Language": st.column_config.TextColumn("Language", width="small"),
                "Time":     st.column_config.TextColumn("Time",     width="large"),
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 2. Lead Cards Grid ──
        st.markdown("#### Recent Enquiries")
        badge_map = {"hot":"badge-hot","warm":"badge-warm","cold":"badge-cold"}
        cols = st.columns(3)
        for i, (_, row) in enumerate(leads_df.iloc[::-1].iterrows()):
            sc  = str(row.get("Score","cold")).lower()
            cls = badge_map.get(sc,"badge-cold")
            with cols[i % 3]:
                st.markdown(f"""
                <div class="lead-entry">
                  <div class="lead-name">&#128100; {row.get('Name','—')}
                    <span class="badge {cls}">{sc.upper()}</span>
                  </div>
                  <div class="lead-meta">&#128241; {row.get('Phone','—')}</div>
                  <div class="lead-meta">&#128231; {row.get('Email','—')}</div>
                  <div><span class="lead-course">{row.get('Course','—')}</span></div>
                  <div class="lead-meta" style="margin-top:5px">&#127760; {row.get('Language','English')} &nbsp;|&nbsp; &#128336; {row.get('Time','—')}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 3. Pie Chart (bottom, compact) ──
        score_counts = leads_df["Score"].value_counts().reset_index()
        score_counts.columns = ["Score", "Count"]
        color_map = {"hot": "#dc2626", "warm": "#ea580c", "cold": "#2563eb"}
        colors = [color_map.get(s, "#64748b") for s in score_counts["Score"]]

        col_chart, col_space = st.columns([1, 1])
        with col_chart:
            fig = go.Figure(go.Pie(
                labels=score_counts["Score"].str.upper(),
                values=score_counts["Count"],
                marker=dict(colors=colors),
                hole=0.5,
                textinfo="label+percent",
                textfont=dict(size=13, family="Sora"),
            ))
            fig.update_layout(
                title="Lead Quality Distribution",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Sora", size=12),
                title_font=dict(size=15, color="#0f172a"),
                height=280,
                margin=dict(l=10, r=10, t=40, b=40),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = leads_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Leads as CSV",
            data=csv_data,
            file_name=f"leads_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )