import streamlit as st
import time
import base64
import uuid
import html
import streamlit.components.v1 as components
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from datetime import datetime

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
    except: return "🔒 [Corrupted Data]"

def strip_exif(img_upload):
    img = Image.open(img_upload)
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
    return clean_img

# --- 2. HRIDAYA COLORS + ADVANCED CSS ---
st.set_page_config(page_title="Hridaya Secure", page_icon="💖", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@300;400;600&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #2d0a0a 0%, #050505 100%);
        color: #ffd1d1;
        font-family: 'Poppins', sans-serif;
    }

    .heart {
        background-color: #ff4d6d; display: inline-block; height: 50px; margin: 0 10px;
        position: relative; top: 0; transform: rotate(-45deg); width: 50px;
        animation: beat 1.2s infinite; box-shadow: 0 0 40px #ff4d6d;
    }
    .heart:before, .heart:after {
        content: ""; background-color: #ff4d6d; border-radius: 50%;
        height: 50px; position: absolute; width: 50px;
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

    [data-testid="stSidebar"] {
        background: rgba(45, 10, 10, 0.7) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 77, 109, 0.3);
    }

    /* Live Header */
    .wa-header {
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
        padding: 10px 15px; display: flex; align-items: center;
        border-radius: 15px 15px 0 0; border: 1px solid rgba(255, 77, 109, 0.3);
        margin-bottom: 0px;
    }
    .wa-avatar {
        width: 42px; height: 42px; border-radius: 50%; background-color: rgba(255,77,109,0.2);
        display: flex; justify-content: center; align-items: center; font-size: 20px; 
        margin-right: 15px; border: 1px solid #ff4d6d; box-shadow: 0 0 10px rgba(255,77,109,0.3);
    }
    .wa-info h3 { margin: 0; font-size: 1.5rem; color: #ff4d6d; font-family: 'Dancing Script', cursive; text-shadow: 0 0 10px rgba(255,77,109,0.5); }
    .wa-info p { margin: 0; font-size: 0.8rem; color: #00ff41; font-weight: bold;}

    /* NATIVE AUTO-SCROLL FIX: column-reverse magic */
    .wa-chat-container {
        display: flex; flex-direction: column-reverse; gap: 8px; padding: 20px;
        background: rgba(0, 0, 0, 0.2); height: 50vh; overflow-y: auto;
        border-left: 1px solid rgba(255, 77, 109, 0.3); border-right: 1px solid rgba(255, 77, 109, 0.3);
    }

    .bubble-me {
        align-self: flex-end; background: rgba(255, 77, 109, 0.15); backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 77, 109, 0.4); color: #fff; padding: 8px 10px 10px 12px;
        border-radius: 15px 0px 15px 15px; max-width: 80%; position: relative; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .bubble-them {
        align-self: flex-start; background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 77, 109, 0.2); color: #ffd1d1; padding: 8px 10px 10px 12px;
        border-radius: 0px 15px 15px 15px; max-width: 80%; position: relative; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* ANTI-SCREENSHOT IMAGE (Phantom Mode) */
    .phantom-img {
        position: relative; display: inline-block; width: 100%; border-radius: 10px; margin-bottom: 5px;
    }
    .phantom-img img {
        opacity: 0; width: 100%; display: block; border-radius: 10px;
        pointer-events: none; border: 1px solid rgba(255,77,109,0.3);
    }
    .phantom-btn {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: rgba(45, 10, 10, 0.9); border: 1px solid #ff4d6d; color: #ff4d6d;
        padding: 8px 15px; border-radius: 20px; font-size: 0.8rem; pointer-events: none;
        box-shadow: 0 0 10px rgba(255,77,109,0.5); white-space: nowrap;
    }
    /* Image appears only when clicked/held or hovered */
    .phantom-img:active img, .phantom-img:hover img { opacity: 1; }
    .phantom-img:active .phantom-btn, .phantom-img:hover .phantom-btn { opacity: 0; }

    .sender-name { font-size: 0.75rem; color: #ff4d6d; font-weight: 600; margin-bottom: 2px; }
    .bubble-me .sender-name { display: none; }
    .msg-text { font-size: 1.05rem; line-height: 1.3; }
    .msg-time { font-size: 0.65rem; color: rgba(255,255,255,0.5); float: right; margin-top: 8px; margin-left: 15px;}

    .wipe-timer {
        height: 2px; background: linear-gradient(90deg, #ff4d6d, transparent);
        width: 100%; position: absolute; bottom: 0; left: 0;
        border-radius: 0 0 10px 10px; animation: shrink 10s linear forwards;
    }
    @keyframes shrink { from { width: 100%; } to { width: 0%; } }

    .stTextInput input {
        background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 77, 109, 0.5) !important;
        border-radius: 30px !important; color: white !important; padding: 12px 20px !important;
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

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 20px;"><div class="heart"></div></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#ff4d6d; font-family:Dancing Script;'>Hridaya Protocol</h2>", unsafe_allow_html=True)
    
    room = st.text_input("💎 PRIVATE FREQUENCY", type="password", placeholder="Secret Key...")
    alias = st.text_input("👤 NICKNAME", value="Shadow")
    
    if room:
        if st.button("🚨 PANIC (Clear Room)", type="primary", use_container_width=True):
            vault["chats"] = [c for c in vault["chats"] if c['room'] != room]
            st.session_state.clear()
            st.rerun()

# --- 5. INTERFACE LOGIC ---
if room:
    key = get_key_from_room(room)

    # Video Call Expander - Bahar rakha hai taaki disconnect na ho
    with st.expander("🎥 Open Private Call"):
        webrtc_streamer(
            key=f"vcall-{room}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            media_stream_constraints={"video": True, "audio": True},
        )

    # FRAGMENT LOGIC: Yaha Member Count aur Chat dono har 2 second me refresh honge!
    @st.fragment(run_every=2)
    def live_chat_feed():
        # Update user presence dynamically
        vault["presence"][st.session_state.uid] = (room, alias, time.time())
        
        # Calculate Live Online Members
        active_members = [name for rid, name, t in vault["presence"].values() if rid == room and time.time() - t < 10]
        unique_members = list(set(active_members))
        online_text = " • ".join(unique_members)
        member_count = len(unique_members)

        # Dynamic Live Header
        st.markdown(f"""
            <div class="wa-header">
                <div class="wa-avatar">💖</div>
                <div class="wa-info">
                    <h3>Hridaya Room</h3>
                    <p>● {member_count} Online | {online_text}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Chat Cleanup (10 sec rule)
        vault["chats"] = [c for c in vault["chats"] if time.time() - c['time'] < 10]
        
        # Get chats for this room
        room_chats = [c for c in vault["chats"] if c['room'] == room]
        
        # CHAT REVERSAL MAGIC: Kyunki CSS me 'column-reverse' hai, 
        # html tag me message ulti direction me generate honge taaki bottom pe automatically chipke rahe!
        room_chats.reverse()
        
        chat_html = '<div class="wa-chat-container">'
        for c in room_chats:
            decrypted = decrypt_msg(c['data'], key)
            safe_text = html.escape(decrypted)
            bubble_class = "bubble-me" if c['user'] == alias else "bubble-them"
            msg_time = datetime.fromtimestamp(c['time']).strftime('%H:%M')
            
            img_html = ""
            if c.get("img"):
                buffered = BytesIO()
                c["img"].save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()
                # Screenshot-proof Phantom Image
                img_html = f"""
                <div class="phantom-img">
                    <div class="phantom-btn">👁️ Hold to View</div>
                    <img src="data:image/jpeg;base64,{img_b64}">
                </div>
                """

            chat_html += f'<div class="{bubble_class}"><div class="sender-name">{c["user"]}</div>{img_html}<div class="msg-text">{safe_text}</div><div class="msg-time">{msg_time} ✓✓</div><div class="wipe-timer"></div></div>'
            
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # Call the live fragment
    live_chat_feed()

    # Input Bar
    st.markdown("<div style='background:rgba(255,255,255,0.05); padding:10px; border-radius:0 0 15px 15px; border: 1px solid rgba(255, 77, 109, 0.3); border-top:none;'>", unsafe_allow_html=True)
    with st.form("input_form", clear_on_submit=True):
        cols = st.columns([0.8, 0.1, 0.1])
        msg = cols[0].text_input("", placeholder="Whisper your heart...")
        img = cols[1].file_uploader("", type=['jpg','png','jpeg'], label_visibility="collapsed")
        send = cols[2].form_submit_button("🕊️")
        
        if send and (msg or img):
            enc_data = encrypt_msg(msg if msg else "📷 Moment Shared", key)
            safe_img = strip_exif(img) if img else None
            vault["chats"].append({
                "room": room, "user": alias, "data": enc_data,
                "img": safe_img, "time": time.time()
            })
            st.rerun() # Submit instantly refreshes the page
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown("""
        <div style="text-align:center; padding:50px; background:rgba(255,77,109,0.05); border-radius:30px; border:1px solid rgba(255,77,109,0.2);">
            <h1 style="font-family:'Dancing Script'; font-size:4rem; color:#ff4d6d;">Welcome, Soulmate</h1>
            <p style="font-size:1.2rem; opacity:0.8;">A place where your words exist only for a moment.</p>
            <hr style="border:1px solid rgba(255,77,109,0.2);">
            <p>Please enter your <b>Private Frequency</b> in the sidebar to enter.</p>
            <div style="font-size:5rem; animation: beat 2s infinite;">💖</div>
        </div>
    """, unsafe_allow_html=True)

# AUTO-LOCK SCRIPT (5 Mins Inactivity)
components.html("""
<script>
    const parent = window.parent;
    if (!parent.inactivityTimerSetup) {
        parent.inactivityTimerSetup = true;
        let timeout;
        function lockProtocol() {
            parent.document.body.innerHTML = `
                <div style="background: #050505; height: 100vh; width: 100vw; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #ff4d6d; font-family: 'Dancing Script', cursive; position: fixed; top: 0; left: 0; z-index: 999999;">
                    <div style="font-size: 6rem; margin-bottom: 20px;">🔒</div>
                    <h1 style="font-size: 4rem; margin: 0; text-shadow: 0 0 20px #ff4d6d;">Connection Severed</h1>
                </div>
            `;
            setTimeout(() => parent.location.reload(), 2000);
        }
        function resetTimer() { clearTimeout(timeout); timeout = setTimeout(lockProtocol, 300000); }
        ['mousemove','mousedown','keypress','touchstart'].forEach(evt => parent.document.addEventListener(evt, resetTimer));
        resetTimer();
    }
</script>
""", height=0, width=0)
