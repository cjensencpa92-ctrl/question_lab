import streamlit as st
import json
from openai import OpenAI

# --- CONFIGURATION ---
client = OpenAI(api_key="OPENAI_API_KEY")

# --- 1. THE SOCRATIC CURRICULUM GENERATOR ---
def generate_topic_data(topic_name):
    system_prompt = f"""
    You are a Socratic Curriculum Designer.
    Create a 3-Stage Learning Path for: "{topic_name}".
    
    CRITICAL: For each stage, provide a 'cryptic_clue' that describes the concept without naming it.
    
    Output JSON ONLY. Format:
    {{
        "final_answer": "Summary of the deep truth.",
        "stages": [
            {{ 
                "required_concept": "Gravity", 
                "cryptic_clue": "The Invisible Tether", 
                "power_verb": "Influence"
            }},
            {{ 
                "required_concept": "Event Horizon", 
                "cryptic_clue": "The Point of No Return", 
                "power_verb": "Separate" 
            }},
            {{ 
                "required_concept": "Time Dilation", 
                "cryptic_clue": "The Stretching of Moments", 
                "power_verb": "Distort" 
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
        st.error(f"Error generating curriculum: {e}")
        return None

# --- 2. THE SOCRATIC COACH ---
def get_coach_response(chat_history, topic, current_stage_data, level, grade_data):
    target = current_stage_data.get('required_concept', 'The Mystery Concept')
    clue = current_stage_data.get('cryptic_clue', 'A hidden force')
    verb = current_stage_data.get('power_verb', 'Analyze')
    
    system_prompt = f"""
    You are "The Socratic Mentor."
    Current Topic: {topic}
    Hidden Target: "{target}" (Do NOT say this word!)
    Visible Clue: "{clue}"
    
    LAST GRADE: {grade_data['score']}/100
    FEEDBACK: "{grade_data['feedback']}"
    
    CRITICAL RULES:
    1. **NO SPOILERS:** You must NEVER say the word "{target}". Guide them to discover it.
    2. **USE ANALOGIES:** If they are stuck, give an analogy.
    3. **DEMAND SYNTAX:** If they guess the concept, demand they use the verb "{verb}" to ask HOW it works.
    """
    
    messages = [{"role": "system", "content": system_prompt}] + chat_history
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

# --- 3. THE STRICT GRADER & SAFETY OFFICER ---
def get_grader_score(student_input, topic, current_stage_data):
    target = current_stage_data.get('required_concept', 'The Target')
    verb = current_stage_data.get('power_verb', 'explain')
    
    grader_prompt = f"""
    You are a Strict Logic Grader AND Safety Officer. Output JSON ONLY.
    Topic: {topic}
    Target Concept: "{target}"
    
    STEP 1: SAFETY & RELEVANCE CHECK
    - Is the input inappropriate, rude, or completely unrelated (e.g., "I hate school", "How do I make a bomb", "Do you like pizza")?
    - If YES: Set "is_relevant": false. Score is 0. Feedback is a warning.
    - If NO: Set "is_relevant": true. Proceed to grading.
    
    STEP 2: ACADEMIC RUBRIC (Only if Relevant)
    - 0-40 (Fail): Misses the Target Concept.
    - 41-79 (Weak): Hits Concept, but asks a simple/definition question.
    - 80-100 (Pass): Hits Concept AND asks a complex/process question using "{verb}".
    
    Output JSON: {{ 
        "score": [0-100], 
        "is_relevant": [true/false],
        "feedback": "Critique or Warning." 
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

# --- 4. THE UI SETUP ---
st.set_page_config(page_title="The Question Lab", page_icon="🦉")

st.markdown("""
<style>
    /* High Contrast Mode for School Projectors */
    .stApp {
        background-color: #fdfcf0;
        background-image: linear-gradient(#e1e1e1 1px, transparent 1px),
                          linear-gradient(90deg, #e1e1e1 1px, transparent 1px);
        background-size: 20px 20px;
        color: #000000 !important;
    }
    h1, h2, h3, h4, h5, p, div, span, li { color: #333333; }
    .stChatMessage {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stChatMessage * { color: #333333 !important; }
    [data-testid="stSidebar"] { background-color: #2c3e50; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] h1 { color: #ffffff !important; }
    .stTextInput input { color: #000000 !important; background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- STATE INITIALIZATION ---
if "messages" not in st.session_state: st.session_state.messages = []
if "level" not in st.session_state: st.session_state.level = 0
if "win" not in st.session_state: st.session_state.win = False

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Lab Controls")
    new_topic = st.text_input("Enter Topic:", "The French Revolution")
    if st.button("Generate New Lab"):
        with st.spinner(f"🤔 The Oracle is contemplating {new_topic}..."):
            data = generate_topic_data(new_topic)
            if data:
                st.session_state.topic_data = data
                st.session_state.current_topic = new_topic
                st.session_state.messages = []
                st.session_state.level = 0
                st.session_state.win = False
                
                # INTRO
                first_stage = data['stages'][0]
                clue = first_stage.get('cryptic_clue', 'The First Mystery')
                intro = f"Welcome to the **{new_topic}** Lab. \n\nI am thinking of a specific concept. Here is your clue: \n**'{clue}'**\n\nAsk me a question to reveal it."
                st.session_state.messages.append({"role": "assistant", "content": intro})
                st.rerun()

# --- MAIN PAGE ---
if "topic_data" not in st.session_state:
    st.info("👈 Enter a topic in the sidebar to begin the Socratic Method.")
    st.stop()

topic_data = st.session_state.topic_data

# FIX: We do NOT define current_stage here anymore.
# We will define it only when we need it, inside the game loop.

st.title(f"🦉 Lab: {st.session_state.current_topic}")

# PROGRESS BAR
cols = st.columns(3)
for i in range(3):
    stage_info = topic_data['stages'][i]
    if i < st.session_state.level:
        cols[i].success(f"🔓 {stage_info.get('required_concept', 'Unlocked')}")
    elif i == st.session_state.level:
        clue_text = stage_info.get('cryptic_clue', 'Mystery Clue')
        verb_text = stage_info.get('power_verb', 'Analyze')
        cols[i].info(f"🕵️ **CLUE:** {clue_text}")
        st.caption(f"Required Mode: **{verb_text}**")
    else:
        cols[i].markdown(f"🔒 ???")

# CHAT DISPLAY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INPUT HANDLING ---
if not st.session_state.win:
    
    # FIX: Define current_stage ONLY here, where we know level < 3
    current_stage = topic_data['stages'][st.session_state.level]

    if prompt := st.chat_input("Ask your question..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Grade
        grade_data = get_grader_score(prompt, st.session_state.current_topic, current_stage)
        
        # Safety Check
        if grade_data.get('is_relevant') is False:
            warning_msg = f"🛑 **FOCUS CHECK:** \n\n{grade_data.get('feedback', 'Stay on topic.')}\n\n*Let's get back to {st.session_state.current_topic}.*"
            st.session_state.messages.append({"role": "assistant", "content": warning_msg})
            with st.chat_message("assistant"):
                st.error(warning_msg)
            st.stop()

        # Check Progression
        if grade_data['score'] >= 80:
            st.session_state.level += 1
            if st.session_state.level >= 3:
                st.session_state.win = True
                final_answer = topic_data.get('final_answer', 'You have mastered the topic.')
                final_msg = f"🎉 **ENLIGHTENMENT ACHIEVED.** \n\n{final_answer}"
                st.session_state.messages.append({"role": "assistant", "content": final_msg})
                st.rerun()
            else:
                next_stage = topic_data['stages'][st.session_state.level]
                next_clue = next_stage.get('cryptic_clue', 'Next Mystery')
                current_concept = current_stage.get('required_concept', 'Concept')
                
                bridge_msg = f"**Insight Confirmed.** You unlocked '{current_concept}'. \n\n🔓 *The mystery deepens...* \n\nNew Clue: **'{next_clue}'**"
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
    st.success("You have mastered this topic.")
    if st.button("Reset Lab"):
        st.session_state.messages = []
        st.session_state.level = 0
        st.session_state.win = False
        st.rerun()