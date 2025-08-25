import streamlit as st
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import io, json, os, hashlib, random
from datetime import datetime

# ---------------- CONFIG -----------------
DATA_FILE = "motifs_registry.json"
os.makedirs("images_challenge", exist_ok=True)

# ---------------- UTILITAIRES -----------------
def save_registry(entry):
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            registry = json.load(f)
    else:
        registry = []
    registry.append(entry)
    with open(DATA_FILE, "w") as f:
        json.dump(registry, f, indent=2)

def load_registry():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def generate_motif(seed=None, size=200):
    if seed is None:
        seed = random.randint(0, 1_000_000)
    random.seed(seed)
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    for _ in range(random.randint(5, 25)):
        shape_type = random.choice(["ellipse","rectangle","line","polygon"])
        x0, y0 = random.randint(0,size), random.randint(0,size)
        x1, y1 = random.randint(0,size), random.randint(0,size)
        x0, x1 = min(x0,x1), max(x0,x1)
        y0, y1 = min(y0,y1), max(y0,y1)

        color = (random.randint(50,255), random.randint(50,255), random.randint(50,255), random.randint(100,220))

        if shape_type=="ellipse":
            draw.ellipse([x0,y0,x1,y1], fill=color)
        elif shape_type=="rectangle":
            draw.rectangle([x0,y0,x1,y1], fill=color)
        elif shape_type=="line":
            draw.line([x0,y0,x1,y1], fill=color, width=random.randint(1,4))
        elif shape_type=="polygon":
            points = [(random.randint(0,size), random.randint(0,size)) for _ in range(random.randint(3,6))]
            draw.polygon(points, fill=color)

    img = img.filter(ImageFilter.GaussianBlur(random.uniform(0,1.5)))
    return img, seed

def apply_motif(image: Image.Image, motif: Image.Image, opacity=0.3):
    motif_resized = motif.resize((image.width, image.height))
    motif_layer = motif_resized.copy()
    alpha = motif_layer.split()[3]
    alpha = alpha.point(lambda p: p * opacity)
    motif_layer.putalpha(alpha)
    combined = Image.alpha_composite(image.convert("RGBA"), motif_layer)
    return combined

def check_motif(original_motif: Image.Image, user_image: Image.Image, threshold=50):
    original = np.array(original_motif.resize(user_image.size).convert("L"))
    user = np.array(user_image.convert("L"))
    diff = np.abs(original.astype(int)-user.astype(int))
    score = 100 - np.mean(diff)/255*100
    return score >= threshold

def sha256_bytes(data: bytes):
    import hashlib
    return hashlib.sha256(data).hexdigest()

# ---------------- STYLE -----------------
st.markdown("""
<style>
body { background-color:#050505; color:#00ff00; font-family:'Courier New', monospace; }
h1,h2,h3,h4,h5,h6 { color:#00ffff; text-shadow:0 0 10px #00ffff,0 0 20px #00ff00; animation:flicker 1.5s infinite alternate; font-weight:bold; }
p, li, span { color:#00ff00; }
.stButton>button { background-color:#111111; color:#00ff00; border:2px solid #00ff00; font-weight:bold; padding:0.5em 1em; text-transform:uppercase; transition:0.3s; }
.stButton>button:hover { background-color:#00ff00; color:#050505; box-shadow:0 0 10px #00ff00,0 0 20px #00ffff,0 0 30px #00ff00 inset; }
.stFileUploader>div { border:2px dashed #00ff00; border-radius:12px; padding:25px; background-color:#111111; transition:0.3s; }
.stFileUploader>div:hover { border-color:#00ffff; box-shadow:0 0 15px #00ff00,0 0 25px #00ffff inset; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input { background-color:#111111; color:#00ff00; border:1px solid #00ff00; border-radius:5px; padding:5px; }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stNumberInput>div>div>input:focus { border-color:#00ffff; outline:none; box-shadow:0 0 10px #00ffff,0 0 20px #00ff00 inset; }
.registry-entry { border:1px solid #00ff00; padding:15px; margin:5px 0; border-radius:8px; background-color:#111111; transition:0.3s; animation: entry-glitch 2s infinite alternate; }
.registry-entry:hover { border-color:#00ffff; box-shadow:0 0 15px #00ff00,0 0 30px #00ffff inset; }
@keyframes flicker { 0% {opacity:0.9; text-shadow:0 0 5px #00ffff;} 50% {opacity:1; text-shadow:0 0 20px #00ff00,0 0 30px #00ffff;} 100% {opacity:0.95; text-shadow:0 0 10px #00ff00,0 0 20px #00ffff;} }
@keyframes entry-glitch { 0% { box-shadow:0 0 10px #00ff00,0 0 20px #00ffff; } 50% { box-shadow:0 0 15px #00ff00,0 0 25px #00ffff inset; } 100% { box-shadow:0 0 12px #00ff00,0 0 22px #00ffff; } }
</style>
""", unsafe_allow_html=True)

st.title("⚡ MOTIF CHALLENGE - trhacknon ⚡")
st.markdown("#### Génération, application et détection de motifs complexes | Dark Mode Hacker")

# ---------------- GENERATION MOTIF -----------------
st.subheader("🔹 Générer un motif unique")
username = st.text_input("Nom / identifiant du membre")
motif_size = st.slider("Taille du motif", 100, 500, 200)
if st.button("Générer motif"):
    user_hash = int(hashlib.sha256(username.encode()).hexdigest(),16) % 1_000_000
    motif_img, seed = generate_motif(seed=user_hash, size=motif_size)
    buf = io.BytesIO()
    motif_img.save(buf, format="PNG")
    buf.seek(0)
    st.image(motif_img, caption=f"Motif généré pour {username}", use_column_width=False)
    st.download_button("Télécharger le motif PNG", buf, file_name=f"motif_{username}.png")
    save_registry({"user":username, "seed":seed, "date":str(datetime.now())})
    st.success(f"Motif généré avec seed {seed} ✅")

# ---------------- APPLICATION MOTIF -----------------
st.subheader("🔹 Appliquer motif sur image")
uploaded_image = st.file_uploader("Choisir image à marquer", type=["png","jpg","jpeg"], key="apply")
uploaded_motif = st.file_uploader("Charger motif PNG", type=["png"], key="motif")
opacity = st.slider("Opacité du motif", 0.05, 1.0, 0.3)
if uploaded_image and uploaded_motif and st.button("Appliquer motif"):
    img = Image.open(uploaded_image).convert("RGBA")
    motif_img = Image.open(uploaded_motif).convert("RGBA")
    combined = apply_motif(img, motif_img, opacity=opacity)
    buf = io.BytesIO()
    combined.save(buf, format="PNG")
    buf.seek(0)
    st.image(combined, caption="Image challenge générée", use_column_width=True)
    st.download_button("Télécharger image challenge", buf, file_name=f"challenge_{uploaded_image.name}")

# ---------------- VERIFICATION MOTIF -----------------
st.subheader("🔹 Vérifier superposition d'un motif")
challenge_image_file = st.file_uploader("Charger image challenge", type=["png","jpg","jpeg"], key="check")
user_motif_file = st.file_uploader("Charger votre motif", type=["png"], key="check_motif")
if challenge_image_file and user_motif_file and st.button("Vérifier motif"):
    challenge_img = Image.open(challenge_image_file).convert("RGBA")
    user_motif_img = Image.open(user_motif_file).convert("RGBA")
    if check_motif(user_motif_img, challenge_img):
        st.success("✅ Motif correctement superposé ! Bravo !")
    else:
        st.error("❌ Motif non détecté ou incorrect.")

# ---------------- HISTORIQUE -----------------
st.subheader("🗂 Historique des motifs générés")
registry = load_registry()
if registry:
    for idx, entry in enumerate(registry):
        st.markdown(f"<div class='registry-entry'>**{idx+1}. {entry['user']}** | seed: {entry['seed']} | date: {entry['date']}</div>", unsafe_allow_html=True)
else:
    st.info("Aucun motif généré pour l'instant.")
