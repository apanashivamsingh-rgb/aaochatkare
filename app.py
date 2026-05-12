import streamlit as st
import time
import base64
import uuid
import streamlit.components.v1 as components
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

# --- 1. ENCRYPTION & PRIVACY ENGINE ---
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

# --- 2. THE "WOW" FACTOR CSS ---
st.set_page_config(page_title="System Portal", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@300;400;600&display=swap');

    .stApp {
        background: radial-gradient(circle at center, #2d0a0a 0%, #050505 100%);
        color: #ffd1d1;
        font-family: 'Poppins', sans-serif;
    }

    /* PEEK-TO-READ BLUR EFFECT */
    .secure-text {
        filter: blur(8px);
        transition: filter 0.3s ease;
        user-select: none;
    }
    .secure-text:hover {
        filter: blur(0px);
        user-select: auto;
    }

    /* PHANTOM IMAGE BUTTON (Hold to View) */
    .phantom-img-container {
        position: relative;
        display: inline-block;
    }
    .phantom-img-container img {
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
    }
    .phantom-btn {
        position: absolute;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(255, 77, 109, 0.2);
        border: 1px solid #ff4d6d;
        color: #ff4d6d;
        padding: 10px 20px;
        border-radius: 20px;
        cursor: pointer;
        z-index: 10;
    }
    .phantom-img-container:hover img {
        opacity: 1;
    }
    .phantom-img-container:hover .phantom-btn {
        opacity: 0;
    }

    .heart {
        background-color: #ff4d6d;
        display: inline-block;
        height: 50px; margin: 0 10px; position: relative; top: 0;
        transform: rotate(-45deg); width: 50px;
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
    .stTextInput input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 77, 109, 0.5) !important;
        border-radius: 30px !important; color: white !important;
    }
    .chat-bubble {
        padding: 20px; border-radius: 25px 25px 25px 5px;
        background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 77, 109, 0.3); margin-bottom: 15px;
    }
    .life-line {
        height: 4px; background: linear-gradient(90deg, #ff4d6d, transparent);
        border-radius: 10px; width: 100%; margin-top: 10px;
        animation: countdown 10s linear forwards;
    }
    @keyframes countdown { from { width: 100%; } to { width: 0%; } }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA VAULT ---
@st.cache_resource
def get_vault():
    return {"chats": [], "presence": {}}

vault = get_vault()

if "uid" not in st.session_state:
    st.session_state.uid = str(uuid.uuid4())[:8]

# --- 4. SIDEBAR & LOGIC ---
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 20px;"><div class="heart"></div></div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#ff4d6d; font-family:Dancing Script;'>Access Portal</h2>", unsafe_allow_html=True)
    
    room = st.text_input("💎 PRIVATE FREQUENCY", type="password", placeholder="Enter Code...")
    alias = st.text_input("👤 NICKNAME", value="Shadow")
    
    # DURESS CHECK (Fake Vault Trigger)
    is_decoy = False
    if room and room.endswith("000"):
        is_decoy = True
        
    if room and not is_decoy:
        vault["presence"][st.session_state.uid] = (room, alias, time.time())
        active_members = [name for rid, name, t in vault["presence"].values() if rid == room and time.time() - t < 10]
        unique_members = list(set(active_members))
        
        members_html = "".join([f"<p style='margin:2px 0; font-size:0.95rem; color:#ffd1d1;'><span style='color:#00ff41; font-size:0.8rem;'>●</span> {m}</p>" for m in unique_members])
        st.markdown(f"""
            <div style='background:rgba(255,77,109,0.1); padding:15px; border-radius:20px; border:1px solid #ff4d6d; text-align:center;'>
                <p style='color:#00ff41; margin:0; font-weight:bold;'>{len(unique_members)} Soul(s) Connected</p>
                <hr style='border-top: 1px solid rgba(255,77,109,0.3); margin: 10px 0;'>
                <div style='text-align:left; padding-left:10px;'>{members_html}</div>
            </div><br>
        """, unsafe_allow_html=True)
        
        if st.button("🚨 PANIC (Kill Switch)", type="primary", use_container_width=True):
            vault["chats"] = [c for c in vault["chats"] if c['room'] != room]
            st.session_state.clear()
            st.rerun()

# --- 5. INTERFACE (DECOY VS REAL) ---
if is_decoy:
    # FAKE UI - Agar code ke last me '000' dala
    st.title("📚 Deep Learning Research Notes")
    st.info("Welcome to the personal study vault. No new updates today.")
    st.markdown("### Topic: Convolutional Neural Networks")
    st.write("CNNs are primarily used for image processing and classification tasks...")
    st.write("Equations: $f(x) = \max(0, x)$ (ReLU Activation function).")
    st.code("import torch\nimport torch.nn as nn\n# Model architecture definition", language="python")

elif room:
    # REAL UI - The actual secure chat
    key = get_key_from_room(room)
    
    # TRAITOR TRACING WATERMARK (Invisible background text)
    st.markdown(f"""
        <div style="position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:9999; pointer-events:none; overflow:hidden; opacity:0.04; font-size:3rem; font-weight:bold; color:white; transform:rotate(-30deg); display:flex; flex-wrap:wrap; justify-content:space-around;">
            {" ".join([alias] * 500)}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='font-family:Dancing Script; font-size:4rem; text-align:center; color:#ff4d6d;'>Hridaya</h1>", unsafe_allow_html=True)

    with st.expander("🎥 Open Private Call"):
        webrtc_streamer(
            key=f"vcall-{room}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            media_stream_constraints={"video": True, "audio": True},
        )

    # 10 Sec Auto-Delete
    vault["chats"] = [c for c in vault["chats"] if time.time() - c['time'] < 10]
    
    for c in [msg for msg in vault["chats"] if msg['room'] == room]:
        decrypted = decrypt_msg(c['data'], key)
        st.markdown(f"""
            <div class='chat-bubble'>
                <small style='color:#ff4d6d; font-weight:bold;'>{c['user']}</small><br>
                <div class='secure-text' style='font-size:1.1rem;'>{decrypted}</div>
                <div class='life-line'></div>
            </div>
        """, unsafe_allow_html=True)
        
        if c.get("img"):
            # PHANTOM IMAGE HTML
            img_b64 = base64.b64encode(c["img"].getvalue()).decode() if hasattr(c["img"], "getvalue") else ""
            if not img_b64:
                buffered = BytesIO()
                c["img"].save(buffered, format="JPEG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()

            st.markdown(f"""
                <div class="phantom-img-container" style="width:100%; text-align:center; background:#111; padding:20px; border-radius:10px;">
                    <div class="phantom-btn">👁️ Hover to View Media</div>
                    <img src="data:image/jpeg;base64,{img_b64}" style="max-width:100%; border-radius:10px;">
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
    with st.container():
        with st.form("input_form", clear_on_submit=True):
            cols = st.columns([0.75, 0.15, 0.1])
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
                st.rerun()

    time.sleep(1)
    st.rerun()
else:
    st.markdown("""
        <div style="text-align:center; padding:50px; background:rgba(255,77,109,0.05); border-radius:30px; border:1px solid rgba(255,77,109,0.2);">
            <h1 style="font-family:'Dancing Script'; font-size:4rem; color:#ff4d6d;">Welcome, Soulmate</h1>
            <p style="font-size:1.2rem; opacity:0.8;">Enter your Frequency to connect.</p>
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
            parent.document.body.innerHTML = '<div style="background:#050505; height:100vh; width:100vw; display:flex; justify-content:center; align-items:center; color:#ff4d6d; font-size:4rem; position:fixed; z-index:999999;">🔒 Connection Severed</div>';
            setTimeout(() => parent.location.reload(), 2000);
        }
        function resetTimer() { clearTimeout(timeout); timeout = setTimeout(lockProtocol, 300000); }
        ['mousemove','mousedown','keypress','touchstart'].forEach(evt => parent.document.addEventListener(evt, resetTimer));
        resetTimer();
    }
</script>
""", height=0, width=0)
