import streamlit as st
import json
import os
from dotenv import load_dotenv
from groq import Groq
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Groq API Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load course data
with open("courses.json", "r") as f:
    courses = json.load(f)

# Page Config
st.set_page_config(
    page_title="AI Enquiry Assistant",
    page_icon="🎓",
    layout="wide"
)

# Header
st.title("🎓 AI Enquiry Assistant")
st.caption("Instant student enquiry & admission assistant")

# -----------------------------
# AI Chat Section
# -----------------------------
user_input = st.text_input(
    "Ask about fees, duration, placements, courses..."
)

if user_input:

    course_info = json.dumps(courses, indent=2)

    prompt = f"""
You are a smart enquiry assistant for a training institute.

Available Courses:
{course_info}

Answer briefly, clearly and professionally.

Student Query:
{user_input}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    st.success(answer)

# -----------------------------
# Lead Form
# -----------------------------
st.divider()
st.subheader("📞 Interested in Joining?")

with st.form("lead_form"):

    name = st.text_input("Full Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")

    course = st.selectbox(
        "Interested Course",
        [c["name"] for c in courses]
    )

    submit = st.form_submit_button("Submit Enquiry")

    if submit:

        data = {
            "Name": [name],
            "Phone": [phone],
            "Email": [email],
            "Course": [course],
            "Time": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }

        new_df = pd.DataFrame(data)

        try:
            old_df = pd.read_csv("leads.csv")
            final_df = pd.concat(
                [old_df, new_df],
                ignore_index=True
            )
        except:
            final_df = new_df

        final_df.to_csv("leads.csv", index=False)

        st.success("✅ Thank you! Our team will contact you soon.")
        st.balloons()

# -----------------------------
# Admin Dashboard
# -----------------------------
st.divider()
st.subheader("📊 Admin Dashboard")

try:
    leads = pd.read_csv("leads.csv")
    st.dataframe(leads, use_container_width=True)
except:
    st.info("No enquiries yet.")