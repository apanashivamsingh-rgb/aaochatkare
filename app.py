import streamlit as st
import time
import base64
import uuid
import html
import hashlib
import streamlit.components.v1 as components
from io import BytesIO
from PIL import Image
from cryptography.fernet import Fernet
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from datetime import datetime

# --- 1. ENCRYPTION ENGINE ---
def get_key_from_room(room_code):
    return base64.urlsafe_b64encode(hashlib.sha256(room_code.encode()).digest())

def encrypt_msg(text, key):
    f = Fernet(key)
    return f.encrypt(text.encode()).decode()

def decrypt_msg(token, key):
    try: return Fernet(key).decrypt(token.encode()).decode()
    except Exception: return "🔒 [Encrypted]"

def strip_exif(img_upload):
    img = Image.open(img_upload)
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
    return clean_img

st.set_page_config(page_title="Hridaya Secure", page_icon="💖", layout="centered")

# --- 2. DATA VAULT ---
@st.cache_resource
def get_vault():
    return {"chats": [], "presence": {}}

vault = get_vault()
if "uid" not in st.session_state:
    st.session_state.uid = str(uuid.uuid4())[:8]

# --- 3. THEME ENGINE ---
stealth = st.sidebar.toggle("🦇 Boss Key (Stealth)", value=False)
rain_mode = st.sidebar.toggle("🌧️ Midnight Rain", value=False)

th_color = "#00ff41" if stealth else "#ff4d6d"
th_glow = "rgba(0, 255, 65, 0.4)" if stealth else "rgba(255, 77, 109, 0.4)"
th_bg = "#010a00" if stealth else "#2d0a0a"
app_title = "Terminal X" if stealth else "Hridaya Protocol"
top_icon = "💻" if stealth else "💖"

st.markdown(f"""
    <style>
    :root {{ --theme-color: {th_color}; --theme-glow: {th_glow}; --theme-bg: {th_bg}; }}
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&family=Poppins:wght@300;400;600&family=Share+Tech+Mono&display=swap');

    .stApp {{ background: radial-gradient(circle at center, var(--theme-bg) 0%, #050505 100%); color: #ffd1d1; font-family: {'"Share Tech Mono", monospace' if stealth else '"Poppins", sans-serif'}; }}

    [data-testid="stExpander"] {{ background: rgba(0, 0, 0, 0.4) !important; border: 1px solid var(--theme-color) !important; border-radius: 15px !important; box-shadow: 0 0 15px var(--theme-glow); margin-bottom: 15px; position:relative; z-index:1; backdrop-filter: blur(10px); }}
    [data-testid="stExpander"] summary {{ color: var(--theme-color) !important; font-weight: 600 !important; }}
    [data-testid="stExpander"] summary svg {{ fill: var(--theme-color) !important; }}

    [data-testid="stSidebar"] {{ background: rgba(0, 0, 0, 0.6) !important; backdrop-filter: blur(20px); border-right: 1px solid var(--theme-glow); z-index: 9999; }}

    .wa-header {{ background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(15px); padding: 12px 20px; display: flex; align-items: center; border-radius: 20px 20px 0 0; border: 1px solid var(--theme-glow); margin-bottom: 0px; box-shadow: 0 5px 20px rgba(0,0,0,0.5); position:relative; z-index:1; }}
    .wa-avatar {{ width: 45px; height: 45px; border-radius: 50%; background-color: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; font-size: 22px; margin-right: 15px; border: 1px solid var(--theme-color); box-shadow: 0 0 15px var(--theme-glow); }}
    .wa-info h3 {{ margin: 0; font-size: 1.6rem; color: var(--theme-color); font-family: {'"Share Tech Mono", monospace' if stealth else '"Dancing Script", cursive'}; text-shadow: 0 0 10px var(--theme-glow); }}
    .wa-info p {{ margin: 0; font-size: 0.85rem; color: #fff; font-weight: 400; opacity:0.9;}}
    .typing-anim {{ display: inline-block; animation: blink 1s infinite; color: var(--theme-color); font-weight: bold; }}
    @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}

    .wa-chat-container {{ display: flex; flex-direction: column-reverse; gap: 15px; padding: 20px; background: rgba(0, 0, 0, 0.15); height: 40vh; overflow-y: auto; border-left: 1px solid var(--theme-glow); border-right: 1px solid var(--theme-glow); position:relative; z-index:1; }}

    @keyframes floatIn {{ 0% {{ opacity: 0; transform: translateY(15px) scale(0.95); }} 100% {{ opacity: 1; transform: translateY(0) scale(1); }} }}

    .bubble-me {{ align-self: flex-end; background: rgba(255, 77, 109, 0.15); backdrop-filter: blur(12px); border: 1px solid rgba(255, 77, 109, 0.5); color: #fff; padding: 12px 16px; border-radius: 20px 0px 20px 20px; max-width: 80%; position: relative; box-shadow: 0 8px 20px rgba(0,0,0,0.3); animation: floatIn 0.3s forwards; transition: 0.3s; }}
    .bubble-them {{ align-self: flex-start; background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(12px); border: 1px solid rgba(255, 77, 109, 0.4); color: #ffd1d1; padding: 12px 16px; border-radius: 0px 20px 20px 20px; max-width: 80%; position: relative; box-shadow: 0 8px 20px rgba(0,0,0,0.3); animation: floatIn 0.3s forwards; transition: 0.3s; }}
    
    .bubble-me:hover {{ transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 25px rgba(255, 77, 109, 0.4); z-index: 10; }}
    .bubble-them:hover {{ transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 25px rgba(255, 77, 109, 0.2); z-index: 10; }}

    .love-letter {{ background: rgba(255, 77, 109, 0.2); border: 1px solid #ff4d6d; border-radius: 10px; padding: 15px; font-family: 'Dancing Script', cursive; font-size: 1.7rem; color: #ffebf0; text-shadow: 0 0 8px rgba(255,77,109,0.6); text-align: center; line-height: 1.4; box-shadow: inset 0 0 25px rgba(255,77,109,0.3); }}
    .code-snippet {{ background: #111; color: #00ff41; padding: 12px; border-radius: 8px; font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; overflow-x: auto; border: 1px solid #333; }}

    .sender-name {{ font-size: 0.75rem; color: var(--theme-color); font-weight: 700; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; }}
    .bubble-me .sender-name {{ display: none; }}
    .msg-text {{ font-size: 1.05rem; line-height: 1.4; letter-spacing: 0.3px; }}
    .msg-time {{ font-size: 0.7rem; color: rgba(255,255,255,0.4); float: right; margin-top: 10px; margin-left: 15px; font-family: monospace; }}
    .tick-read {{ color: #00ff41; font-weight: bold; text-shadow: 0 0 5px #00ff41; }}
    .tick-unread {{ color: gray; }}

    .wipe-timer {{ height: 3px; background: linear-gradient(90deg, var(--theme-color), transparent); width: 100%; position: absolute; bottom: 0; left: 0; border-radius: 0 0 15px 15px; animation-name: shrink; animation-timing-function: linear; animation-fill-mode: forwards; }}
    @keyframes shrink {{ from {{ width: 100%; }} to {{ width: 0%; }} }}

    .stTextInput input {{ background: rgba(0, 0, 0, 0.4) !important; border: 1px solid var(--theme-glow) !important; border-radius: 30px !important; color: white !important; padding: 14px 20px !important; box-shadow: inset 0 0 10px rgba(0,0,0,0.5); font-size: 1.05rem; }}
    
    /* 🔥 BEAUTIFUL MAGICAL UPLOAD ICON (STARDUST) 🔥 */
    [data-testid="stFileUploader"] {{ width: 45px !important; margin: 0 auto; display: flex; align-items: center; justify-content: center; }}
    [data-testid="stFileUploader"] section {{ background: rgba(255, 77, 109, 0.1) !important; border: 2px solid var(--theme-color) !important; border-radius: 50% !important; height: 45px !important; width: 45px !important; padding: 0 !important; display: flex; justify-content: center; align-items: center; cursor: pointer; box-shadow: 0 0 10px var(--theme-glow); transition: 0.3s; position: relative; overflow: hidden; }}
    [data-testid="stFileUploader"] section:hover {{ background: rgba(255, 77, 109, 0.3) !important; box-shadow: 0 0 25px var(--theme-color); transform: scale(1.15) rotate(15deg); }}
    [data-testid="stFileUploader"] section::before {{ content: "✨"; font-size: 22px; position: absolute; text-shadow: 0 0 10px #fff; }}
    [data-testid="stFileUploader"] .css-17xejub, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] .css-9ycgxx, [data-testid="stFileUploader"] svg, [data-testid="stFileUploader"] span {{ display: none !important; opacity: 0; }}

    /* GIANT BEATING HEART ANIMATION */
    @keyframes big-beat {{
        0% {{ transform: translate(-50%, -50%) scale(1); opacity: 0.8; filter: drop-shadow(0 0 30px #ff4d6d); }}
        20% {{ transform: translate(-50%, -50%) scale(1.3); opacity: 1; filter: drop-shadow(0 0 80px #ff4d6d); }}
        40% {{ transform: translate(-50%, -50%) scale(1.1); opacity: 0.9; filter: drop-shadow(0 0 50px #ff4d6d); }}
        60% {{ transform: translate(-50%, -50%) scale(1.4); opacity: 1; filter: drop-shadow(0 0 100px #ff4d6d); }}
        100% {{ transform: translate(-50%, -50%) scale(1); opacity: 0; filter: drop-shadow(0 0 10px #ff4d6d); }}
    }}
    
    @keyframes screen-pulse {{
        0% {{ box-shadow: inset 0 0 0px rgba(255, 77, 109, 0); }}
        25% {{ box-shadow: inset 0 0 100px rgba(255, 77, 109, 0.8); }}
        50% {{ box-shadow: inset 0 0 20px rgba(255, 77, 109, 0.4); }}
        75% {{ box-shadow: inset 0 0 150px rgba(255, 77, 109, 0.9); background: rgba(255,77,109,0.1); }}
        100% {{ box-shadow: inset 0 0 0px rgba(255, 77, 109, 0); }}
    }}
    .heartbeat-active {{ animation: screen-pulse 1.2s ease-in-out !important; }}
    </style>
""", unsafe_allow_html=True)

# 🌧️ 100% RELIABLE PURE JS/CSS RAIN (NO GIFs, NO DOGS!)
if rain_mode and not stealth:
    components.html("""
        <script>
            const parent = window.parent.document;
            if (!parent.getElementById('css-rain-layer')) {
                const rc = parent.createElement('div');
                rc.id = 'css-rain-layer';
                rc.style = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;overflow:hidden;mix-blend-mode:screen;';
                for(let i=0; i<150; i++) {
                    let drop = parent.createElement('div');
                    drop.style = `position:absolute; background:linear-gradient(transparent, rgba(255,255,255,0.4)); width:1px; height:${Math.random()*40+30}px; left:${Math.random()*100}vw; top:-100px; animation: rain-fall ${Math.random()*0.5 + 0.3}s linear infinite;`;
                    rc.appendChild(drop);
                }
                parent.body.appendChild(rc);
                
                if(!parent.getElementById('rain-anim')) {
                    const style = parent.createElement('style');
                    style.id = 'rain-anim';
                    style.innerHTML = '@keyframes rain-fall { 0% { transform: translateY(-10vh); opacity:0;} 50% {opacity:1;} 100% { transform: translateY(110vh); opacity:0; } }';
                    parent.head.appendChild(style);
                }
            }
        </script>
    """, height=0)
else:
    components.html("<script>const r = window.parent.document.getElementById('css-rain-layer'); if(r) r.remove();</script>", height=0)

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:var(--theme-color); font-size:4.5rem; text-shadow: 0 0 30px var(--theme-glow);'>{top_icon}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; color:var(--theme-color); font-family:inherit; margin-top:-10px;'>{app_title}</h2><br>", unsafe_allow_html=True)
    
    room_input = st.text_input("💎 PRIVATE FREQUENCY", type="password", placeholder="Secret Key...")
    alias = st.text_input("👤 NICKNAME", value="Romeo")
    room = room_input
    
    if room_input and room_input.endswith("-BURN"):
        st.error("⚠️ FATAL ERROR 404")
        st.stop()
    
    if room:
        vault["presence"][st.session_state.uid] = (room, alias, time.time())
        active_members = [name for rid, name, t in vault["presence"].values() if rid == room and time.time() - t < 10]
        
        st.markdown(f"""
            <div style='background:rgba(0,0,0,0.4); padding:15px; border-radius:20px; border:1px solid var(--theme-color); text-align:center; box-shadow: inset 0 0 15px var(--theme-glow);'>
                <p style='color:var(--theme-color); margin:0; font-size:1.1rem; font-weight:bold;'>{len(set(active_members))} Souls Connected</p>
                <hr style='border-top: 1px solid var(--theme-glow); margin: 10px 0;'>
                <div style='text-align:left; padding-left:10px;'>
                    {"".join([f"<p style='margin:4px 0; font-size:1rem; color:#fff;'><span style='color:var(--theme-color); font-size:0.8rem; text-shadow: 0 0 5px var(--theme-color);'>●</span> {m}</p>" for m in set(active_members)])}
                </div>
            </div><br>
        """, unsafe_allow_html=True)
            
        with st.expander("🎵 Romantic Vibe Sync"):
            components.html('<iframe style="border-radius:12px" src="https://open.spotify.com/embed/playlist/37i9dQZF1DX0XUfTFmUMB1?utm_source=generator&theme=0" width="100%" height="152" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>', height=160)

        if st.button("🚨 DESTROY MEMORIES", type="primary", use_container_width=True):
            vault["chats"] = [c for c in vault["chats"] if c['room'] != room]
            st.session_state.clear()
            st.rerun()

# --- 5. INTERFACE LOGIC ---
if room:
    key = get_key_from_room(room)
    
    with st.expander("📞 Secure Call Hub"):
        call_type = st.radio("Call Mode:", ["Video + Audio", "Audio Only"], horizontal=True)
        webrtc_streamer(key=f"vcall-{room}", mode=WebRtcMode.SENDRECV, rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}), media_stream_constraints={"video": True if "Video" in call_type else False, "audio": True})

    @st.fragment(run_every=2)
    def live_chat_feed():
        vault["presence"][st.session_state.uid] = (room, alias, time.time())
        active_members = [name for rid, name, t in vault["presence"].values() if rid == room and time.time() - t < 10]
        typing_anim = '<span class="typing-anim">typing...</span>' if len(set(active_members)) > 1 else "Online"
        
        st.markdown(f"""
            <div class="wa-header">
                <div class="wa-avatar">{top_icon}</div>
                <div class="wa-info">
                    <h3>{app_title}</h3>
                    <p>● {len(set(active_members))} {typing_anim}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        new_chats = []
        for c in vault["chats"]:
            if c.get("is_pinned"): new_chats.append(c)
            else:
                ttl = 4 if c.get("is_snap") else 10
                if time.time() - c['time'] < ttl: new_chats.append(c)
        vault["chats"] = new_chats
        
        room_chats = [c for c in vault["chats"] if c['room'] == room]
        room_chats.reverse()
        
        chat_html = '<div class="wa-chat-container">'
        heartbeat_trigger = False
        is_read = len(set(active_members)) > 1
        tick_class = "tick-read" if is_read else "tick-unread"
        
        for c in room_chats:
            decrypted = decrypt_msg(c['data'], key)
            
            # HIDDEN REAL HEARTBEAT & SOUND DETECTION
            if "[[HEARTBEAT_SYNC]]" in decrypted:
                if time.time() - c['time'] < 2: heartbeat_trigger = True
                continue 
                
            safe_text = html.escape(decrypted)
            bubble_class = "bubble-me" if c['user'] == alias else "bubble-them"
            msg_time = datetime.fromtimestamp(c['time']).strftime('%H:%M')
            anim_dur = 3 if c.get("is_snap") else 10
            
            if c.get("is_love_letter"): safe_text = f'<div class="love-letter">{safe_text.replace(chr(10), "<br>")}</div>'
            elif c.get("is_code"): safe_text = f'<div class="code-snippet">{safe_text.replace(chr(10), "<br>")}</div>'
            
            media_html = ""
            if c.get("file_b64"):
                ext = c.get("file_ext", "FILE").lower()
                if ext in ['jpg','jpeg','png']:
                    media_html = f'<img src="data:image/jpeg;base64,{c["file_b64"]}" style="width:100%; border-radius:10px; border:1px solid var(--theme-glow); margin-bottom:5px;">'
                elif ext in ['mp4', 'mov', 'webm']:
                    media_html = f'<video controls style="width:100%; border-radius:10px; border:1px solid var(--theme-color);" src="data:video/{ext};base64,{c["file_b64"]}"></video>'
                elif ext in ['mp3', 'wav', 'ogg']:
                    media_html = f'<audio controls style="width:100%; height:35px; outline:none; margin-bottom:5px;" src="data:audio/{ext};base64,{c["file_b64"]}"></audio>'
                else:
                    media_html = f'<a href="data:application/octet-stream;base64,{c["file_b64"]}" download="Secure_{ext.upper()}" style="text-decoration:none;"><div style="background:rgba(0,0,0,0.5); padding:12px; border-radius:10px; border:1px solid var(--theme-color); color:#fff; text-align:center; font-weight:bold; transition:0.3s;">📁 Download .{ext.upper()}</div></a>'

            pin_badge = "📌 " if c.get("is_pinned") else ""
            timer_html = "" if c.get("is_pinned") else f'<div class="wipe-timer" style="animation-duration: {anim_dur}s;"></div>'

            chat_html += f'<div class="{bubble_class}"><div class="sender-name">{c["user"]}</div>{media_html}<div class="msg-text">{safe_text}</div><div class="msg-time">{pin_badge}{msg_time} <span class="{tick_class}">✓✓</span></div>{timer_html}</div>'
            
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # MAGIC: Play Sound and Show Giant Heart!
        if heartbeat_trigger:
            components.html("""
            <script>
                const p = window.parent.document;
                
                // Play heartbeat audio (Google public library)
                const audio = new Audio("https://actions.google.com/sounds/v1/human_voices/heartbeat.ogg");
                audio.play().catch(e => console.log("Audio blocked by browser, requires user interaction first."));
                
                // Show Giant Heart
                const heart = p.createElement('div');
                heart.innerHTML = "💖";
                heart.style = "position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); font-size:18rem; z-index:999999; animation: big-beat 1.5s forwards; pointer-events:none;";
                p.body.appendChild(heart);
                
                // Pulse Background
                p.body.classList.add('heartbeat-active');
                
                // Clean up after 1.5 seconds
                setTimeout(() => { 
                    p.body.classList.remove('heartbeat-active'); 
                    if(heart) heart.remove(); 
                }, 1500);
            </script>
            """, height=0, width=0)
        
    live_chat_feed()

    # NAYA FIX: TOUCH HEARTBEAT BUTTON
    st.markdown("<div style='background:rgba(255,255,255,0.02); padding:15px; border-radius:0 0 20px 20px; border: 1px solid var(--theme-glow); border-top:none; box-shadow: 0 10px 30px rgba(0,0,0,0.6);'>", unsafe_allow_html=True)
    
    if st.button("💓 Tap to Sync Heartbeat", use_container_width=True):
        vault["chats"].append({"room": room, "user": alias, "data": encrypt_msg("[[HEARTBEAT_SYNC]]", key), "time": time.time(), "is_snap": False, "is_pinned": False})
        st.rerun()

    with st.form("input_form", clear_on_submit=True):
        opt_cols = st.columns(4)
        is_love_letter = opt_cols[0].checkbox("💌 Love Letter")
        is_code = opt_cols[1].checkbox("🖥️ Code")
        is_snap = opt_cols[2].checkbox("🧨 3-Sec Snap")
        is_pinned = opt_cols[3].checkbox("📌 Pin")
        
        # BEAUTIFUL MAGICAL UPLOADER (No more ugly box!)
        cols = st.columns([0.7, 0.15, 0.15])
        msg = cols[0].text_input("", placeholder="Whisper your heart...", autocomplete="off")
        upload_file = cols[1].file_uploader("", label_visibility="collapsed")
        send = cols[2].form_submit_button("➤")
        
        if send and (msg or upload_file):
            file_b64 = None; file_ext = ""
            if upload_file:
                file_ext = upload_file.name.split('.')[-1].lower() if '.' in upload_file.name else "file"
                if file_ext in ['jpg', 'jpeg', 'png']:
                    buffered = BytesIO(); strip_exif(upload_file).save(buffered, format="JPEG")
                    file_b64 = base64.b64encode(buffered.getvalue()).decode()
                else:
                    file_b64 = base64.b64encode(upload_file.getvalue()).decode()

            enc_data = encrypt_msg(msg if msg else f"📂 Attached .{file_ext.upper()}", key)
            vault["chats"].append({
                "room": room, "user": alias, "data": enc_data, "is_love_letter": is_love_letter, 
                "is_snap": is_snap, "is_code": is_code, "is_pinned": is_pinned,
                "file_b64": file_b64, "file_ext": file_ext, "time": time.time()
            })
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown(f"""
        <div style="text-align:center; padding:50px; background:rgba(0,0,0,0.6); border-radius:30px; border:1px solid var(--theme-color); box-shadow: 0 0 50px var(--theme-glow); position:relative; z-index:1; backdrop-filter:blur(10px);">
            <h1 style="font-size:4.5rem; color:var(--theme-color); font-family:inherit; text-shadow: 0 0 25px var(--theme-color); margin-bottom: 0;">{app_title}</h1>
            <p style="font-size:1.3rem; opacity:0.9; color: #fff; letter-spacing:1px;">Encrypted. Ephemeral. Yours.</p>
            <hr style="border:1px solid var(--theme-glow); margin: 25px 0;">
            <p style="font-size: 1.1rem; color: #ffd1d1;">Enter your <b>Private Frequency</b> to connect.</p>
            <div style="font-size:6rem; text-shadow: 0 0 40px var(--theme-color); animation: beat 1.5s infinite;">{top_icon}</div>
        </div>
    """, unsafe_allow_html=True)
