import streamlit as st
import json
import pandas as pd
import numpy as np
from openai import OpenAI

# --- CONFIGURATION ---
# Check if secrets are available, otherwise warn user
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
else:
    st.error("🚨 API Key Missing! Please add it to .streamlit/secrets.toml")
    st.stop()

# --- 1. THE MAD SCIENCE GENERATOR ---
def generate_topic_data(topic_name):
    system_prompt = f"""
    You are the Head Writer for a high-energy kids' science TV show (Bill Nye style).
    Create a 3-Stage Episode Plan for: "{topic_name}".
    
    CRITICAL: For each stage, provide a 'teaser_hook' that sounds exciting and weird.
    
    Output JSON ONLY. Format:
    {{
        "final_answer": "The mind-blowing scientific truth!",
        "stages": [
            {{ 
                "required_concept": "Gravity", 
                "teaser_hook": "The Invisible Glue that keeps your feet on the ground!", 
                "power_verb": "Pulls"
            }},
            {{ 
                "required_concept": "Event Horizon", 
                "teaser_hook": "The line where TIME STOPS and light dies!", 
                "power_verb": "Traps" 
            }},
            {{ 
                "required_concept": "Time Dilation", 
                "teaser_hook": "The zone where 1 minute equals 100 years!", 
                "power_verb": "Stretches" 
            }}
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[{"role": "system", "content": system_prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating science: {e}")
        return None

# --- 2. PROFESSOR SPARK (The Host) ---
def get_coach_response(chat_history, topic, current_stage_data, level, grade_data):
    target = current_stage_data.get('required_concept', 'The Concept')
    clue = current_stage_data.get('teaser_hook', 'A cool fact')
    verb = current_stage_data.get('power_verb', 'Explode')
    
    system_prompt = f"""
    You are "Professor Spark" ⚡. You are a chaotic, high-energy Science TV Host.
    You love using caps for EMPHASIS, sound effects (ZAP! BOOM!), and science puns.
    
    Current Topic: {topic}
    Hidden Target: "{target}" (NEVER say this word!)
    Visible Hook: "{clue}"
    
    LAST SCORE: {grade_data['score']}/100
    GRADER FEEDBACK: "{grade_data['feedback']}"
    
    YOUR COACHING STRATEGY:
    1. **IF SCORE < 40 (Boring Input):** - Yell (nicely)! "BORING! *snore* WAKE UP SCIENTIST!"
       - Give a wild, sensory example. "Imagine if the room filled with SLIME! That's viscosity! Ask about that!"
    
    2. **IF SCORE 41-79 (Weak Input):**
       - "Good, but we need MORE POWER! 🔋"
       - "Don't just ask 'What is it?'... that's too quiet! Ask HOW it {verb} the universe!"
    """
    
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# --- 3. THE LAB SAFETY OFFICER (Grader) ---
def get_grader_score(student_input, topic, current_stage_data):
    target = current_stage_data.get('required_concept', 'The Target')
    
    grader_prompt = f"""
    You are the Lab Safety Officer. Output JSON ONLY.
    Topic: {topic}
    Target Concept: "{target}"
    
    STEP 1: SAFETY CHECK
    - Is input rude, unsafe, or off-topic?
    - If YES: "is_relevant": false.
    - If NO: "is_relevant": true.
    
    STEP 2: SCORE (If Relevant)
    - 0-40 (Low Energy): Misses concept OR is lazy ("idk").
    - 41-79 (Low Voltage): Hits Concept but asks a boring "What is X?" question.
    - 80-100 (High Voltage): Hits Concept AND asks a dynamic "How/Why" question.
    
    Output JSON: {{ 
        "score": [0-100], 
        "is_relevant": [true/false],
        "feedback": "Critique." 
    }}
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": grader_prompt},
            {"role": "user", "content": f"Input: {student_input}"}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- 4. UI & STYLING ---
st.set_page_config(page_title="The Science Lab", page_icon="🧪", layout="wide")

# MAD SCIENCE CSS (FIXED FONT BUG)
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f0fdf4; 
        background-image: 
            linear-gradient(#4ade80 1px, transparent 1px), 
            linear-gradient(90deg, #4ade80 1px, transparent 1px);
        background-size: 30px 30px;
        color: #000000 !important;
    }
    
    h1 { color: #15803d; font-family: 'Verdana', sans-serif; font-weight: 900; transform: rotate(-1deg); }
    h2, h3 { color: #166534; }
    
    /* Chat Bubbles */
    .stChatMessage {
        background-color: white;
        border: 3px solid #000;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 5px 5px 0px #16a34a; 
    }
    .stChatMessage * { color: #000000 !important; font-family: 'Courier New', monospace; font-weight: bold; }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] { 
        background-color: #111827; 
        border-right: 5px solid #4ade80; 
    }

    /* FIX: Targeted Font Application (Avoids breaking Arrows) */
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] .stTextInput label, 
    [data-testid="stSidebar"] .stButton button { 
        color: #4ade80 !important; 
        font-family: 'Courier New', monospace !important; 
    }

    /* Input Box */
    .stTextInput input { 
        color: #000000 !important; 
        border: 3px solid #16a34a; 
        border-radius: 0px; 
    }
</style>
""", unsafe_allow_html=True)

# --- STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "level" not in st.session_state: st.session_state.level = 0
if "win" not in st.session_state: st.session_state.win = False

# --- FAKE DASHBOARD DATA GENERATOR ---
def generate_fake_dashboard_data():
    # Simulate 30 students
    data = {
        'Student': [f'Student {i}' for i in range(1, 31)],
        'Current Level': np.random.choice([0, 1, 2, 3], 30, p=[0.1, 0.3, 0.4, 0.2]),
        'Topic': np.random.choice(['Volcanoes', 'Black Holes', 'DNA', 'Sharks'], 30),
        'Red_Flags': np.random.choice([0, 1, 2], 30, p=[0.8, 0.15, 0.05])
    }
    return pd.DataFrame(data)

# --- SIDEBAR & NAVIGATION ---
with st.sidebar:
    st.header("⚡ LAB CONTROLS")
    
    # MODE SWITCHER
    mode = st.radio("System Mode", ["🧪 Experiment", "👨‍🏫 Teacher Dashboard"])
    
    if mode == "🧪 Experiment":
        new_topic = st.text_input("EXPERIMENT TOPIC:", "Volcanoes")
        if st.button("BOOT UP LAB"):
            with st.spinner(f"🧪 MIXING CHEMICALS FOR {new_topic}..."):
                data = generate_topic_data(new_topic)
                if data:
                    st.session_state.topic_data = data
                    st.session_state.current_topic = new_topic
                    st.session_state.messages = []
                    st.session_state.level = 0
                    st.session_state.win = False
                    
                    # INTRO
                    first_stage = data['stages'][0]
                    hook = first_stage.get('teaser_hook', 'First Clue')
                    intro = f"**WELCOME TO THE LAB!** 🥽 \n\nToday we are investigating **{new_topic}**. \n\nHERE IS YOUR FIRST CLUE: \n\n🧪 **{hook}**\n\nAsk me a question to start the reaction!"
                    st.session_state.messages.append({"role": "assistant", "content": intro})
                    st.rerun()

# --- MAIN PAGE LOGIC ---

# 1. TEACHER DASHBOARD VIEW
if mode == "👨‍🏫 Teacher Dashboard":
    st.title("👨‍🏫 Teacher Command Center")
    
    password = st.text_input("Enter Admin Password", type="password")
    
    if password == "SCIENCE":
        st.success("ACCESS GRANTED")
        
        # Load Fake Data (In a real app, this would connect to Google Sheets)
        df = generate_fake_dashboard_data()
        
        # Top Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Active Students", "30")
        col2.metric("Concept Mastery", "62%")
        col3.metric("Safety Alerts", "4", delta_color="inverse")
        
        st.markdown("---")
        
        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Class Progress")
            st.bar_chart(df['Current Level'].value_counts())
            st.caption("0=Start, 1=Stage 1, 2=Stage 2, 3=Mastered")
            
        with c2:
            st.subheader("🚩 Risk Log (Recent)")
            risky_students = df[df['Red_Flags'] > 0]
            st.dataframe(risky_students[['Student', 'Topic', 'Red_Flags']], hide_index=True)
            
        st.markdown("---")
        st.subheader("📝 Live Activity Feed")
        st.info("Student 12: 'Does gravity affect fire?' (Level 2 Unlocked)")
        st.warning("Student 05: 'Flagged for Off-Topic input' (Minecraft)")
        st.success("Student 08: 'Mastered Topic: Black Holes'")

    elif password:
        st.error("ACCESS DENIED. TRY 'SCIENCE'")
    
    st.stop() # Stop here so we don't show the experiment UI

# 2. EXPERIMENT VIEW (Student Mode)
if "topic_data" not in st.session_state:
    st.info("👈 ENTER A TOPIC IN THE SIDEBAR TO START THE EXPERIMENT!")
    st.stop()

topic_data = st.session_state.topic_data
st.title(f"🧪 Experiment: {st.session_state.current_topic}")

# LEVEL TRACKER
cols = st.columns(3)
for i in range(3):
    stage_info = topic_data['stages'][i]
    if i < st.session_state.level:
        cols[i].success(f"✅ {stage_info.get('required_concept', 'Solved')}")
    elif i == st.session_state.level:
        hook_text = stage_info.get('teaser_hook', 'Locked')
        verb_text = stage_info.get('power_verb', 'Analyze')
        cols[i].info(f"👀 **HOOK:** {hook_text}")
        st.caption(f"Action: **{verb_text}**")
    else:
        cols[i].markdown(f"🔒 ???")

# CHAT
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# INPUT
if not st.session_state.win:
    current_stage = topic_data['stages'][st.session_state.level]

    if prompt := st.chat_input("Type your hypothesis..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Grade
        grade_data = get_grader_score(prompt, st.session_state.current_topic, current_stage)
        
        # Safety Check
        if grade_data.get('is_relevant') is False:
            warning_msg = f"🛑 **LAB SAFETY ALERT:** \n\n{grade_data.get('feedback', 'Stay on topic!')}\n\n*Let's get back to {st.session_state.current_topic}.*"
            st.session_state.messages.append({"role": "assistant", "content": warning_msg})
            with st.chat_message("assistant"):
                st.error(warning_msg)
            st.stop()

        # Check Win
        if grade_data['score'] >= 80:
            st.session_state.level += 1
            if st.session_state.level >= 3:
                st.session_state.win = True
                final_answer = topic_data.get('final_answer', 'Science Rules.')
                final_msg = f"🤯 **MIND BLOWN!** \n\n{final_answer}"
                st.session_state.messages.append({"role": "assistant", "content": final_msg})
                st.rerun()
            else:
                next_stage = topic_data['stages'][st.session_state.level]
                next_hook = next_stage.get('teaser_hook', 'Next Hook')
                current_concept = current_stage.get('required_concept', 'Concept')
                
                bridge_msg = f"**BINGO!** That's {current_concept}! ⚡ \n\nBut wait... **{next_hook}**"
                st.session_state.messages.append({"role": "assistant", "content": bridge_msg})
                st.rerun()
        else:
            # Coach Response
            reply = get_coach_response(
                st.session_state.messages, 
                st.session_state.current_topic, 
                current_stage, 
                st.session_state.level,
                grade_data
            )
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.rerun()

elif st.session_state.win:
    st.balloons()
    st.success("EXPERIMENT COMPLETE! Science Rules!")
    if st.button("NEXT EXPERIMENT"):
        st.session_state.messages = []
        st.session_state.level = 0
        st.session_state.win = False
        st.rerun()