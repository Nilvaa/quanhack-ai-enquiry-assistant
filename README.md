EduPath – AI Enquiry Assistant
QuAnHack Internship Final Round Submission
An AI-powered enquiry assistant for training academies. Handles student queries, recommends courses, captures leads, and simulates automated follow-up via WhatsApp and email.
Live Demo: https://quanhack-ai-enquiry-assistant.streamlit.app/

What It Does

Answers student questions about courses, fees, placements, and batch dates
Recommends the best course based on the student's goal
Compares two courses side by side when asked
Captures lead details (name, phone, email) through a validated inline form
Scores leads automatically as Hot, Warm, or Cold
Shows a simulated WhatsApp message and email that would be sent after enrollment
Supports both English and Malayalam
Admin dashboard with lead table, cards, and pie chart analytics


How It Works
Student Message
      |
Language Detection (English / Malayalam)
      |
Groq LLaMA 3.1 with conversation memory
      |
Intent Classification
      |-- Course Enquiry    --> Answer from knowledge base
      |-- Recommendation   --> Ask goal, suggest best match
      |-- Comparison        --> Side-by-side table
      |-- Enrollment Intent --> Show lead capture form
      |
Form Validation --> Save Lead to CSV
      |
Auto Lead Scoring (Hot / Warm / Cold)
      |
Follow-up Preview (WhatsApp + Email)
      |
Admin Dashboard

Tech Stack
LayerTechnologyAI / LLMGroq — LLaMA 3.1 8B InstantFrontendStreamlitStylingCustom CSSBackendPython 3.10+DataPandas, CSVChartsPlotlyHostingStreamlit Community Cloud
