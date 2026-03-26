import pickle
import re
import string
from typing import Union

import streamlit as st

# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GuardMail · Spam Intelligence",
    page_icon="🛡️",
    layout="centered",
)

LABEL_NAMES = {0: "Normal", 1: "Promotional", 2: "Scam/Spam"}

# ── Styling ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@400;500;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Cabinet Grotesk', sans-serif;
    box-sizing: border-box;
}
.stApp {
    background-color: #080c14;
    color: #e8eaf0;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(99,179,237,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,179,237,0.04) 1px, transparent 1px);
    background-size: 44px 44px;
    pointer-events: none;
    z-index: 0;
}
.block-container {
    position: relative;
    z-index: 1;
    max-width: 780px !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
}

/* Header */
.gm-badge {
    display: block;
    text-align: center;
    margin-bottom: 1rem;
}
.gm-badge span {
    display: inline-block;
    background: linear-gradient(135deg, rgba(99,179,237,0.12), rgba(159,122,234,0.12));
    border: 1px solid rgba(99,179,237,0.25);
    border-radius: 999px;
    padding: 0.35rem 1.1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    color: #63b3ed;
    text-transform: uppercase;
}
.gm-title {
    text-align: center;
    font-size: 3.4rem;
    font-weight: 900;
    letter-spacing: -2px;
    line-height: 1.0;
    margin: 0 0 0.6rem;
    background: linear-gradient(135deg, #e8eaf0 30%, #63b3ed 70%, #9f7aea 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.gm-subtitle {
    text-align: center;
    color: #5a6478;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    margin-bottom: 0;
}

/* Stats strip */
.stats-strip {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    margin: 2rem 0 2.5rem;
    padding: 1.1rem 2rem;
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
}
.stat-item { text-align: center; }
.stat-val { font-size: 1.4rem; font-weight: 800; color: #63b3ed; line-height: 1; }
.stat-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #4a5568;
    text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.2rem;
}

/* Input */
.input-label {
    font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: #4a5568; margin-bottom: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
}
textarea {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
    background-color: rgba(255,255,255,0.03) !important;
    color: #e8eaf0 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    caret-color: #63b3ed !important;
    line-height: 1.6 !important;
}
textarea:focus {
    border-color: rgba(99,179,237,0.4) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.08) !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #2b6cb0 0%, #553c9a 100%) !important;
    color: #fff !important;
    font-family: 'Cabinet Grotesk', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.03em !important;
    width: 100%;
    box-shadow: 0 4px 20px rgba(43,108,176,0.25) !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(43,108,176,0.4) !important;
}

/* ── Result card — rendered as three separate st.markdown calls ── */
/* Top: icon + pill + heading + desc + confidence */
.card-top-normal {
    background: linear-gradient(135deg, #0a1f14 0%, #0d2b1a 100%);
    border: 1px solid rgba(72,187,120,0.3);
    border-bottom: none;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 0 40px rgba(72,187,120,0.07);
    padding: 1.8rem 2rem 1.2rem;
}
.card-top-promo {
    background: linear-gradient(135deg, #0e1428 0%, #141a38 100%);
    border: 1px solid rgba(99,179,237,0.3);
    border-bottom: none;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 0 40px rgba(99,179,237,0.07);
    padding: 1.8rem 2rem 1.2rem;
}
.card-top-scam {
    background: linear-gradient(135deg, #1a0a0a 0%, #250d0d 100%);
    border: 1px solid rgba(245,101,101,0.35);
    border-bottom: none;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 0 40px rgba(245,101,101,0.08);
    padding: 1.8rem 2rem 1.2rem;
}

/* Middle: probability bars */
.card-mid-normal {
    background: linear-gradient(135deg, #0a1f14 0%, #0d2b1a 100%);
    border-left: 1px solid rgba(72,187,120,0.3);
    border-right: 1px solid rgba(72,187,120,0.3);
    padding: 0.8rem 2rem 1.2rem;
}
.card-mid-promo {
    background: linear-gradient(135deg, #0e1428 0%, #141a38 100%);
    border-left: 1px solid rgba(99,179,237,0.3);
    border-right: 1px solid rgba(99,179,237,0.3);
    padding: 0.8rem 2rem 1.2rem;
}
.card-mid-scam {
    background: linear-gradient(135deg, #1a0a0a 0%, #250d0d 100%);
    border-left: 1px solid rgba(245,101,101,0.35);
    border-right: 1px solid rgba(245,101,101,0.35);
    padding: 0.8rem 2rem 1.2rem;
}

/* Bottom: closing cap */
.card-bot-normal {
    background: linear-gradient(135deg, #0a1f14 0%, #0d2b1a 100%);
    border: 1px solid rgba(72,187,120,0.3);
    border-top: none;
    border-radius: 0 0 16px 16px;
    height: 16px;
}
.card-bot-promo {
    background: linear-gradient(135deg, #0e1428 0%, #141a38 100%);
    border: 1px solid rgba(99,179,237,0.3);
    border-top: none;
    border-radius: 0 0 16px 16px;
    height: 16px;
}
.card-bot-scam {
    background: linear-gradient(135deg, #1a0a0a 0%, #250d0d 100%);
    border: 1px solid rgba(245,101,101,0.35);
    border-top: none;
    border-radius: 0 0 16px 16px;
    height: 16px;
}

/* Inside card elements */
.card-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.8rem;
}
.card-icon { font-size: 2.6rem; line-height: 1; }
.verdict-pill {
    display: inline-block;
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-size: 0.73rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace;
}
.pill-normal  { background: rgba(72,187,120,0.15);  color: #68d391; border: 1px solid rgba(72,187,120,0.25); }
.pill-promo   { background: rgba(99,179,237,0.15);  color: #63b3ed; border: 1px solid rgba(99,179,237,0.25); }
.pill-scam    { background: rgba(245,101,101,0.15); color: #fc8181; border: 1px solid rgba(245,101,101,0.25); }

.result-heading {
    font-size: 2rem; font-weight: 900;
    letter-spacing: -0.5px; margin: 0 0 0.3rem; line-height: 1.1;
}
.h-normal { color: #68d391; }
.h-promo  { color: #63b3ed; }
.h-scam   { color: #fc8181; }

.result-desc {
    font-size: 0.92rem; color: #718096;
    line-height: 1.5; margin-bottom: 1.2rem;
}
.conf-row {
    display: flex; align-items: baseline;
    gap: 0.5rem; margin-bottom: 0.3rem;
}
.conf-number { font-size: 3rem; font-weight: 900; letter-spacing: -2px; line-height: 1; }
.conf-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #4a5568;
    text-transform: uppercase; letter-spacing: 0.08em;
}
.cn-normal { color: #68d391; }
.cn-promo  { color: #63b3ed; }
.cn-scam   { color: #fc8181; }

/* Prob bars */
.prob-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: #4a5568;
    margin-bottom: 0.7rem;
}
.prob-row {
    display: flex; align-items: center;
    gap: 0.9rem; margin-bottom: 0.6rem;
}
.prob-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem; color: #718096;
    width: 96px; flex-shrink: 0;
}
.prob-bar-bg {
    flex: 1; background: rgba(255,255,255,0.05);
    border-radius: 999px; height: 7px; overflow: hidden;
}
.prob-bar-fill { height: 7px; border-radius: 999px; }
.fill-normal { background: linear-gradient(90deg, #38a169, #68d391); }
.fill-promo  { background: linear-gradient(90deg, #2b6cb0, #63b3ed); }
.fill-scam   { background: linear-gradient(90deg, #c53030, #fc8181); }
.prob-pct {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; font-weight: 500;
    width: 44px; text-align: right; flex-shrink: 0;
}
.pct-normal { color: #68d391; }
.pct-promo  { color: #63b3ed; }
.pct-scam   { color: #fc8181; }

/* Pre-processing expander */
.pre-block {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.pre-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: #4a5568; margin-bottom: 0.4rem;
}
.pre-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: #a0aec0;
    line-height: 1.6; word-break: break-all;
}
.pre-text-blue { color: #63b3ed; }
.pre-steps {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #2d3748;
    margin-top: 0.5rem; line-height: 1.7;
}

/* Warning */
.warn-box {
    background: rgba(236,153,75,0.07);
    border: 1px solid rgba(236,153,75,0.2);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: #d69e2e; line-height: 1.5;
}

/* Divider / Footer */
.gm-divider { border: none; border-top: 1px solid rgba(255,255,255,0.05); margin: 2rem 0; }
.gm-footer {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; color: #2d3748;
    padding: 0.5rem 0; letter-spacing: 0.08em; text-transform: uppercase;
}

/* Streamlit cleanup */
.stTextArea label { display: none; }
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    margin-top: 1.2rem !important;
}
[data-testid="stExpander"] summary {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: #4a5568 !important;
    padding: 0.75rem 1rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Stopwords ──────────────────────────────────────────────────────────────────

try:
    import nltk
    from nltk.corpus import stopwords
    nltk.download('stopwords', quiet=True)
    STOPWORDS = set(stopwords.words('english'))
except ImportError:
    STOPWORDS = {
        'i','me','my','myself','we','our','ours','ourselves','you','your','yours',
        'yourself','yourselves','he','him','his','himself','she','her','hers',
        'herself','it','its','itself','they','them','their','theirs','themselves',
        'what','which','who','whom','this','that','these','those','am','is','are',
        'was','were','be','been','being','have','has','had','having','do','does',
        'did','doing','a','an','the','and','but','if','or','because','as','until',
        'while','of','at','by','for','with','about','against','between','into',
        'through','during','before','after','above','below','to','from','up','down',
        'in','out','on','off','over','under','again','further','then','once','here',
        'there','when','where','why','how','all','both','each','few','more','most',
        'other','some','such','no','nor','not','only','own','same','so','than','too',
        'very','s','t','can','will','just','don','should','now','d','ll','m','o',
        're','ve','y','ain','aren','couldn','didn','doesn','hadn','hasn','haven',
        'isn','ma','mightn','mustn','needn','shan','shouldn','wasn','weren','won','wouldn'
    }

# ── clean_text ─────────────────────────────────────────────────────────────────

def clean_text(
    text: Union[str, list],
    lowercase: bool = True,
    remove_punct: bool = True,
    remove_stops: bool = True,
    remove_nums: bool = False,
    remove_url: bool = True,
    custom_stopwords: set = None,
) -> Union[str, list]:
    if isinstance(text, list):
        return [clean_text(t, lowercase, remove_punct, remove_stops,
                           remove_nums, remove_url, custom_stopwords) for t in text]
    if not isinstance(text, str):
        raise TypeError(f"Expected str or list, got {type(text).__name__}")
    if remove_url:
        text = re.sub(r'http\S+|www\S+', '', text)
    if lowercase:
        text = text.lower()
    if remove_nums:
        text = re.sub(r'\d+', '', text)
    if remove_punct:
        text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    if remove_stops:
        stop_words = STOPWORDS | custom_stopwords if custom_stopwords else STOPWORDS
        text = ' '.join(w for w in text.split() if w not in stop_words)
    return text

# ── Load Model ─────────────────────────────────────────────────────────────────

@st.cache_resource
def load_artifacts():
    with open('spam_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('tfidf_vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    return model, vectorizer

try:
    model, vectorizer = load_artifacts()
    model_loaded = True
except FileNotFoundError as e:
    model_loaded = False
    load_error = str(e)

# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="gm-badge"><span>🛡️ GuardMail · Spam Intelligence v2.0</span></div>', unsafe_allow_html=True)
st.markdown('<div class="gm-title">Is it spam?</div>', unsafe_allow_html=True)
st.markdown('<div class="gm-subtitle">TF-IDF · LOGISTIC REGRESSION · 3-CLASS CLASSIFIER</div>', unsafe_allow_html=True)

st.markdown("""
<div class="stats-strip">
    <div class="stat-item"><div class="stat-val">3</div><div class="stat-lbl">Classes</div></div>
    <div class="stat-item"><div class="stat-val">3K</div><div class="stat-lbl">TF-IDF Features</div></div>
    <div class="stat-item"><div class="stat-val">LR</div><div class="stat-lbl">Algorithm</div></div>
    <div class="stat-item"><div class="stat-val">&lt;1s</div><div class="stat-lbl">Inference</div></div>
</div>
""", unsafe_allow_html=True)

if not model_loaded:
    st.markdown(f'<div class="warn-box">⚠️ Model files not found. Place <code>spam_classifier.pkl</code> and <code>tfidf_vectorizer.pkl</code> alongside <code>app.py</code>.<br><br>Error: {load_error}</div>', unsafe_allow_html=True)
    st.stop()

# ── Input ──────────────────────────────────────────────────────────────────────

st.markdown('<div class="input-label">📨 &nbsp; Message to Analyse</div>', unsafe_allow_html=True)

user_input = st.text_area(
    label="Message",
    placeholder="Paste or type a message here — SMS, email subject, push notification…",
    height=150,
    label_visibility="collapsed",
)

predict_clicked = st.button("🔍  Analyse Message")

# ── Prediction ─────────────────────────────────────────────────────────────────

if predict_clicked:
    if not user_input.strip():
        st.markdown('<div class="warn-box">⚠️ Please enter a message before analysing.</div>', unsafe_allow_html=True)
    else:
        cleaned = clean_text(user_input)
        vec = vectorizer.transform([cleaned])
        prediction = int(model.predict(vec)[0])
        proba = model.predict_proba(vec)[0]

        normal_pct = round(float(proba[0]) * 100, 1)
        promo_pct  = round(float(proba[1]) * 100, 1)
        scam_pct   = round(float(proba[2]) * 100, 1)
        conf_pct   = [normal_pct, promo_pct, scam_pct][prediction]

        cfg = {
            0: dict(
                key="normal", pill_cls="pill-normal", head_cls="h-normal", conf_cls="cn-normal",
                icon="✅", pill="Normal", heading="Looks Legit",
                desc="This message appears to be genuine, personal, or transactional. No suspicious patterns detected.",
            ),
            1: dict(
                key="promo", pill_cls="pill-promo", head_cls="h-promo", conf_cls="cn-promo",
                icon="🛍️", pill="Promotional", heading="Promotional",
                desc="This looks like a promotional message from a legitimate brand — offers or discounts, but not a scam.",
            ),
            2: dict(
                key="scam", pill_cls="pill-scam", head_cls="h-scam", conf_cls="cn-scam",
                icon="🚫", pill="Scam / Spam", heading="Spam Detected",
                desc="This message shows strong characteristics of spam or a scam. May be phishing or fraudulent. Proceed with caution.",
            ),
        }
        c = cfg[prediction]
        k = c["key"]

        # ── TOP section of card ────────────────────────────────────────────────
        st.markdown(
            f'<div class="card-top-{k}">'
            f'  <div class="card-header-row">'
            f'    <div class="card-icon">{c["icon"]}</div>'
            f'    <div class="verdict-pill {c["pill_cls"]}">{c["pill"]}</div>'
            f'  </div>'
            f'  <div class="result-heading {c["head_cls"]}">{c["heading"]}</div>'
            f'  <div class="result-desc">{c["desc"]}</div>'
            f'  <div class="conf-row">'
            f'    <div class="conf-number {c["conf_cls"]}">{conf_pct}%</div>'
            f'    <div class="conf-label">confidence</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── MIDDLE section — probability bars ──────────────────────────────────
        st.markdown(
            f'<div class="card-mid-{k}">'
            f'  <div class="prob-section-label">Probability Breakdown</div>'
            f'  <div class="prob-row">'
            f'    <div class="prob-name">✅ Normal</div>'
            f'    <div class="prob-bar-bg"><div class="prob-bar-fill fill-normal" style="width:{normal_pct}%"></div></div>'
            f'    <div class="prob-pct pct-normal">{normal_pct}%</div>'
            f'  </div>'
            f'  <div class="prob-row">'
            f'    <div class="prob-name">🛍️ Promo</div>'
            f'    <div class="prob-bar-bg"><div class="prob-bar-fill fill-promo" style="width:{promo_pct}%"></div></div>'
            f'    <div class="prob-pct pct-promo">{promo_pct}%</div>'
            f'  </div>'
            f'  <div class="prob-row">'
            f'    <div class="prob-name">🚫 Scam</div>'
            f'    <div class="prob-bar-bg"><div class="prob-bar-fill fill-scam" style="width:{scam_pct}%"></div></div>'
            f'    <div class="prob-pct pct-scam">{scam_pct}%</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── BOTTOM cap ─────────────────────────────────────────────────────────
        st.markdown(f'<div class="card-bot-{k}"></div>', unsafe_allow_html=True)

        # ── Preprocessing expander ─────────────────────────────────────────────
        with st.expander("🔬  Preprocessing detail"):
            raw_display   = user_input[:400] + ("…" if len(user_input) > 400 else "")
            clean_display = (cleaned[:400] + ("…" if len(cleaned) > 400 else "")) if cleaned else "(empty after cleaning)"
            st.markdown(
                f'<div class="pre-block"><div class="pre-label">Raw Input</div>'
                f'<div class="pre-text">{raw_display}</div></div>'
                f'<div class="pre-block"><div class="pre-label">After Cleaning (fed to TF-IDF)</div>'
                f'<div class="pre-text pre-text-blue">{clean_display}</div></div>'
                f'<div class="pre-steps">Steps: URL removal → lowercasing → punctuation stripping → stopword removal → whitespace normalization</div>',
                unsafe_allow_html=True,
            )

# ── Footer ─────────────────────────────────────────────────────────────────────

st.markdown('<hr class="gm-divider">', unsafe_allow_html=True)
st.markdown('<div class="gm-footer">GuardMail · Logistic Regression · TF-IDF (3 000 features) · 3-class · Streamlit</div>', unsafe_allow_html=True)