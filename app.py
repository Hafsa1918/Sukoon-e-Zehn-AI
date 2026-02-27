import gradio as gr
import sqlite3
import pandas as pd
from database import init_db, signup_user, login_user, save_and_plot, DB_FILE
from engine import sukoon_app

init_db()

# FULL EXPANDED SYLLABUS
FULL_SYLLABUS = {
    "Student (Self-Care)": {
        "Core Concepts": [
            ("Lec 1: Understanding Anxiety", "NWv1VdDeoRY", "Identifying physical and mental symptoms."),
            ("Lec 2: The Science of Sleep", "t0kACis_dJE", "How sleep impacts cognitive performance."),
            ("Lec 3: Dealing with Burnout", "DxIDKZHW3-E", "Recovery steps for academic exhaustion.")
        ],
        "Practical Tools": [
            ("Lec 4: Mindfulness Techniques", "ZToicYcHIOU", "Simple exercises for daily calm."),
            ("Lec 5: Focus & Flow State", "IAtw_m988S4", "Methods to enhance concentration."),
            ("Lec 6: Digital Detox", "Czg_9C7gw0o", "Managing social media's impact on mood.")
        ]
    },
    "Teacher (Psychology)": {
        "Student Support": [
            ("Lec 1: Child Development", "8nz2dtv--ok", "Key milestones in emotional growth."),
            ("Lec 2: Identifying Dyslexia", "hS_V_E9UeYQ", "Spotting learning gaps early."),
            ("Lec 3: Trauma in Schools", "fS4X1E6-f-4", "Creating safe spaces for students.")
        ],
        "Teacher Wellness": [
            ("Lec 4: Managing Classroom Stress", "N7on_u2p9fI", "Staying calm in high-pressure environments."),
            ("Lec 5: Avoiding Educator Burnout", "79U_S6mNq_A", "Setting boundaries for work-life balance."),
            ("Lec 6: Collaborative Care", "KY5TWV_5ZDU", "Working with parents and psychologists.")
        ]
    },
    "Manager (Workplace)": {
        "Leadership Skills": [
            ("Lec 1: Emotional Intelligence", "W_vM8_Fp6_M", "Building empathy in professional teams."),
            ("Lec 2: Psychological Safety", "LhoLuui9gX8", "Creating trust within organizations."),
            ("Lec 3: EQ as a Superpower", "uInm_fM-L8I", "Leading through change and crisis.")
        ],
        "Office Culture": [
            ("Lec 4: Resolving Conflict", "KY5TWV_5ZDU", "Mediation techniques for managers."),
            ("Lec 5: Productive Boundaries", "NWv1VdDeoRY", "Promoting a healthy work-life balance."),
            ("Lec 6: Reducing Burnout", "DxIDKZHW3-E", "Structural changes for mental wellness.")
        ]
    }
}

def book_appt(user, doctor, dt):
    if not user: return None
    try:
        clean_time = pd.to_datetime(dt).strftime('%Y-%m-%d %I:%M %p') if dt else pd.Timestamp.now().strftime('%Y-%m-%d %I:%M %p')
    except:
        clean_time = pd.Timestamp.now().strftime('%Y-%m-%d %I:%M %p')

    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("INSERT INTO appointments VALUES (?, ?, ?, ?, ?)", (user, doctor, "SehatYab", clean_time, "Confirmed"))
    conn.commit()
    df = pd.read_sql_query(f"SELECT doctor as 'Doctor', date_time as 'Time', status as 'Status' FROM appointments WHERE username='{user}'", conn)
    conn.close()
    return df

CSS = """
.video-frame { aspect-ratio: 16/9; width: 100%; border-radius: 12px; overflow: hidden; background: #000; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.emergency-banner { 
    background-color: #ffcccc; 
    border: 2px solid #d32f2f; 
    padding: 15px; 
    border-radius: 10px; 
    text-align: center; 
    margin-bottom: 10px;
    animation: blink 2s infinite;
}
@keyframes blink { 0% {opacity: 1;} 50% {opacity: 0.7;} 100% {opacity: 1;} }
"""

with gr.Blocks(title="Sukoon-e-Zehn", css=CSS) as demo:
    logged_in_user = gr.State(None)

    # AUTHENTICATION BOX
    with gr.Column() as auth_box:
        gr.Markdown("# 🧠 Sukoon-e-Zehn AI\n### Pakistan's Premier AI Mental Health Platform")
        with gr.Tabs():
            with gr.TabItem("Login"):
                l_user = gr.Textbox(label="Username"); l_pass = gr.Textbox(label="Password", type="password")
                l_btn = gr.Button("Login", variant="primary")
            with gr.TabItem("Sign Up"):
                s_user = gr.Textbox(label="New Username"); s_pass = gr.Textbox(label="New Password", type="password")
                s_btn = gr.Button("Create Account")
        auth_msg = gr.Markdown()

    # MAIN APPLICATION
    with gr.Column(visible=False) as main_app:
        with gr.Row():
            user_display = gr.Markdown()
            logout_btn = gr.Button("Logout", size="sm", variant="secondary")

        with gr.Tabs():
            # 1. SUPPORT CHAT (With LangGraph & Emergency Banner)
            with gr.TabItem("💬 Support Chat"):
                crisis_banner = gr.HTML(visible=False)
                chatbot = gr.Chatbot()
                msg_input = gr.Textbox(placeholder="Talk to us...", label="Message")
                audio_out = gr.Audio(label="Voice Reply", autoplay=True)
                
                def chat_func(msg, hist):
                    # Invoke LangGraph
                    result = sukoon_app.invoke({"messages": [{"role":"user","content":msg}]})
                    
                    hist.append({"role":"user","content":msg})
                    hist.append({"role":"assistant","content":result['final_response']})
                    
                    # LangGraph ke is_crisis flag par banner update
                    if result.get('is_crisis'):
                        banner_html = """
                        <div class="emergency-banner">
                            <h2 style="color: #d32f2f; margin: 0;">⚠️ EMERGENCY: CALL UMANG HELPLINE</h2>
                            <h1 style="color: #d32f2f; margin: 5px 0;">0311-7786264</h1>
                            <p style="color: black;">Aap tanha nahi hain. Hum aapke saath hain.</p>
                        </div>
                        """
                        return hist, result['audio_path'], gr.update(value=banner_html, visible=True)
                    
                    return hist, result['audio_path'], gr.update(visible=False)

                msg_input.submit(chat_func, [msg_input, chatbot], [chatbot, audio_out, crisis_banner])

            # 2. EDUCATOR TAB (Full Sidebar Layout)
            with gr.TabItem("🏫 Educator"):
                with gr.Row():
                    with gr.Column(scale=1): # SIDEBAR
                        role_drop = gr.Dropdown(choices=list(FULL_SYLLABUS.keys()), label="Select Track", value="Student (Self-Care)")
                        @gr.render(inputs=role_drop)
                        def render_sidebar(role):
                            with gr.Column():
                                for category, lectures in FULL_SYLLABUS[role].items():
                                    with gr.Accordion(category, open=True):
                                        for title, vid, desc in lectures:
                                            btn = gr.Button(f"▶ {title}", variant="secondary", size="sm")
                                            btn.click(lambda v=vid, t=title, d=desc: (
                                                f"### {t}",
                                                f'<div class="video-frame"><iframe width="100%" height="100%" src="https://www.youtube.com/embed/{v}?autoplay=1" frameborder="0" allowfullscreen></iframe></div>',
                                                f"**Overview:** {d}"
                                            ), None, [v_title, v_frame, v_desc])
                    
                    with gr.Column(scale=3): # MAIN CONTENT
                        v_title = gr.Markdown("### Training Portal")
                        v_frame = gr.HTML('<div class="video-frame" style="display:flex; align-items:center; justify-content:center; color:#fff;">Select a lesson from the sidebar</div>')
                        v_desc = gr.Markdown("_Details will appear here._")

            # 3. WELLNESS TAB
            with gr.TabItem("📈 Wellness"):
                with gr.Row():
                    with gr.Column():
                        m_sl = gr.Slider(1, 10, label="Mood", value=5); s_sl = gr.Slider(1, 10, label="Stress", value=5)
                        sl_n = gr.Number(label="Sleep", value=8)
                        save_btn = gr.Button("Log Health Data", variant="primary")
                        status_msg = gr.Markdown()
                    with gr.Column():
                        plt_out = gr.Plot(container=True)
                save_btn.click(save_and_plot, [logged_in_user, s_sl, m_sl, sl_n], [plt_out, status_msg])

            # 4. APPOINTMENTS
            with gr.TabItem("📅 Appointments"):
                with gr.Row():
                    with gr.Column():
                        doc = gr.Dropdown(["Dr. Sarah", "Dr. Ahmed", "Dr. Faisal"], label="Specialist")
                        dt = gr.DateTime(label="Select Date/Time")
                        b_btn = gr.Button("Book Confirmed", variant="primary")
                    with gr.Column():
                        appt_table = gr.Dataframe(interactive=False)
                b_btn.click(book_appt, [logged_in_user, doc, dt], appt_table)

    def login_handler(u, p):
        if login_user(u, p): return gr.update(visible=False), gr.update(visible=True), u, f"### Welcome, {u}"
        return gr.update(visible=True), gr.update(visible=False), None, "❌ Invalid credentials"

    l_btn.click(login_handler, [l_user, l_pass], [auth_box, main_app, logged_in_user, user_display])
    s_btn.click(signup_user, [s_user, s_pass], auth_msg)
    logout_btn.click(lambda: (gr.update(visible=True), gr.update(visible=False), None), None, [auth_box, main_app, logged_in_user])

demo.launch()