import streamlit as st
import time
import base64
import uuid
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# --- 1. ENCRYPTION ENGINE ---
def get_key_from_room(room_code):
    return base64.urlsafe_b64encode(room_code.ljust(32)[:32].encode())

def encrypt_msg(text, key):
    f = Fernet(key)
    return f.encrypt(text.encode()).decode()

def decrypt_msg(token, key):
    try:
        f = Fernet(key)
        return f.decrypt(token.encode()).decode()
    except: return "🔒 [Security Protocol Active]"

# --- 2. THE "WOW" FACTOR CSS ---
st.set_page_config(page_title="Hridaya Elite", page_icon="💖", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@300;400;600&display=swap');

    /* Background Animation */
    .stApp {
        background: radial-gradient(circle at center, #2d0a0a 0%, #050505 100%);
        color: #ffd1d1;
        font-family: 'Poppins', sans-serif;
    }

    /* Floating Heart Animation */
    .heart {
        background-color: #ff4d6d;
        display: inline-block;
        height: 50px;
        margin: 0 10px;
        position: relative;
        top: 0;
        transform: rotate(-45deg);
        width: 50px;
        animation: beat 1.2s infinite;
        box-shadow: 0 0 40px #ff4d6d;
    }
    .heart:before, .heart:after {
        content: "";
        background-color: #ff4d6d;
        border-radius: 50%;
        height: 50px;
        position: absolute;
        width: 50px;
    }
    .heart:before { top: -25px; left: 0; }
    .heart:after { left: 25px; top: 0; }

    @keyframes beat {
        0% { transform: scale(1) rotate(-45deg); }
        20% { transform: scale(1.25) rotate(-45deg); }
        40% { transform: scale(1.1) rotate(-45deg); }
        60% { transform: scale(1.35) rotate(-45deg); }
        100% { transform: scale(1) rotate(-45deg); }
    }

    /* Beautiful Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(45, 10, 10, 0.7) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 77, 109, 0.3);
    }

    /* Custom Chat Bar */
    .stTextInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 77, 109, 0.5) !important;
        border-radius: 30px !important;
        color: white !important;
        padding: 10px 25px !important;
    }

    /* Chat Bubbles */
    .chat-bubble {
        padding: 20px;
        border-radius: 25px 25px 25px 5px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 77, 109, 0.3);
        margin-bottom: 15px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }

    .header-text {
        font-family: 'Dancing Script', cursive;
        font-size: 4rem;
        text-align: center;
        color: #ff4d6d;
        text-shadow: 0 0 20px rgba(255, 77, 109, 0.5);
    }
    
    .life-line {
        height: 4px;
        background: linear-gradient(90deg, #ff4d6d, transparent);
        border-radius: 10px;
        width: 100%;
        margin-top: 10px;
        animation: countdown 10s linear forwards;
    }
    @keyframes countdown { from { width: 100%; } to { width: 0%; } }

    /* Welcome Screen */
    .welcome-container {
        text-align: center;
        padding: 50px;
        background: rgba(255, 77, 109, 0.05);
        border-radius: 30px;
        border: 1px solid rgba(255, 77, 109, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA VAULT ---
@st.cache_resource
def get_vault():
    return {"chats": [], "presence": {}}

vault = get_vault()

if "uid" not in st.session_state:
    st.session_state.uid = str(uuid.uuid4())[:8]

# --- 4. SIDEBAR DESIGN ---
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 20px;"><div class="heart"></div></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#ff4d6d; font-family:Dancing Script;'>Love Protocol</h2>", unsafe_allow_html=True)
    
    room = st.text_input("💎 PRIVATE FREQUENCY", type="password", placeholder="Secret Key...")
    alias = st.text_input("👤 NICKNAME", value="Shadow")
    
    if room:
        vault["presence"][st.session_state.uid] = (room, time.time())
        active = sum(1 for rid, t in vault["presence"].values() if rid == room and time.time() - t < 10)
        st.markdown(f"""
            <div style='background:rgba(255,77,109,0.1); padding:15px; border-radius:20px; border:1px solid #ff4d6d; text-align:center;'>
                <p style='color:#00ff41; margin:0;'>● Connected</p>
                <p style='margin:0;'>{active} Active in Room</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔴 Wipe Memories"):
            vault["chats"] = [c for c in vault["chats"] if c['room'] != room]
            st.rerun()

# --- 5. INTERFACE LOGIC ---
if room:
    key = get_key_from_room(room)
    st.markdown("<h1 class='header-text'>Hridaya</h1>", unsafe_allow_html=True)

    # Video Line
    with st.expander("🎥 Open Private Call"):
        webrtc_streamer(
            key=f"vcall-{room}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            media_stream_constraints={"video": True, "audio": True},
        )

    # Chat Sync & Cleanup
    vault["chats"] = [c for c in vault["chats"] if time.time() - c['time'] < 10]
    
    for c in [msg for msg in vault["chats"] if msg['room'] == room]:
        decrypted = decrypt_msg(c['data'], key)
        st.markdown(f"""
            <div class='chat-bubble'>
                <small style='color:#ff4d6d; font-weight:bold;'>{c['user']}</small><br>
                <div style='font-size:1.1rem;'>{decrypted}</div>
                <div class='life-line'></div>
            </div>
        """, unsafe_allow_html=True)
        if c.get("img"):
            st.image(c["img"], use_container_width=True)

    # Advanced Chat Bar
    st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
    with st.container():
        with st.form("input_form", clear_on_submit=True):
            cols = st.columns([0.75, 0.15, 0.1])
            msg = cols[0].text_input("", placeholder="Whisper your heart...")
            img = cols[1].file_uploader("", type=['jpg','png','jpeg'], label_visibility="collapsed")
            send = cols[2].form_submit_button("🕊️")
            
            if send and (msg or img):
                enc_data = encrypt_msg(msg if msg else "📷 Moment Shared", key)
                vault["chats"].append({
                    "room": room, "user": alias, "data": enc_data,
                    "img": Image.open(img) if img else None, "time": time.time()
                })
                st.rerun()

    time.sleep(1)
    st.rerun()
else:
    # Beautiful First Page
    st.markdown("""
        <div class="welcome-container">
            <h1 style="font-family:'Dancing Script'; font-size:4rem; color:#ff4d6d;">Welcome, Soulmate</h1>
            <p style="font-size:1.2rem; opacity:0.8;">A place where your words exist only for a moment.</p>
            <hr style="border:1px solid rgba(255,77,109,0.2);">
            <p>Please enter your <b>Private Frequency</b> in the sidebar to enter.</p>
            <div style="font-size:5rem; animation: beat 2s infinite;">💖</div>
        </div>
    """, unsafe_allow_html=True)