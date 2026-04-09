# ============================================================
# app.py — VerifyIt: Can You Beat the Machine?
# ============================================================

import streamlit as st
import json
import random
import time

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="VerifyIt",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# LOAD CLIP DATA
# ============================================================

@st.cache_data
def load_clip_data():
    with open("clip_scores.json", "r") as f:
        return json.load(f)

clips = load_clip_data()

# ============================================================
# SESSION STATE
# ============================================================

if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.current_clip = None
    st.session_state.clip_index = 0
    st.session_state.score = 0
    st.session_state.skill = 5.0
    st.session_state.answered = False
    st.session_state.player_guess = None
    st.session_state.history = []
    st.session_state.used_clips = []
    st.session_state.game_over = False
    st.session_state.score_updated = False

# ============================================================
# HELPERS
# ============================================================

def get_next_clip():
    available = [
        c for c in clips
        if c["filename"] not in st.session_state.used_clips
    ]
    if not available:
        available = clips
        st.session_state.used_clips = []
    if st.session_state.clip_index == 0:
        return random.choice(available)
    available.sort(key=lambda c: abs(c["difficulty"] - st.session_state.skill))
    top_matches = available[:min(5, len(available))]
    return random.choice(top_matches)


def update_skill(correct):
    if correct:
        st.session_state.skill = min(10.0, st.session_state.skill + 0.5)
    else:
        st.session_state.skill = max(1.0, st.session_state.skill - 0.5)


def get_result_message(player_correct, model_correct):
    if player_correct and model_correct:
        return "You and the AI both nailed it.", "both_right"
    elif player_correct and not model_correct:
        return "You beat the AI on this one.", "player_wins"
    elif not player_correct and model_correct:
        return "The AI got this one. You didn't.", "ai_wins"
    else:
        return "Neither of you got it right.", "both_wrong"


def get_drive_embed_url(video_url):
    if "id=" in video_url:
        file_id = video_url.split("id=")[1]
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return video_url


def reset_game():
    st.session_state.game_started = False
    st.session_state.current_clip = None
    st.session_state.clip_index = 0
    st.session_state.score = 0
    st.session_state.skill = 5.0
    st.session_state.answered = False
    st.session_state.player_guess = None
    st.session_state.history = []
    st.session_state.used_clips = []
    st.session_state.game_over = False
    st.session_state.score_updated = False


# ============================================================
# CSS — RETRO GROOVY THEME
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background-color: #FFF8F0 !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}

    /* Override Streamlit default fonts */
    .stMarkdown, .stMarkdown p, .stMarkdown li {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #1A1A1A;
    }

    /* ── Title Screen ── */
    .hero {
        text-align: center;
        padding: 48px 24px 32px 24px;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 48px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.03em;
        margin-bottom: 12px;
    }

    .hero-accent {
        color: #E85D04;
    }

    .hero-subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 18px;
        color: #6B6B6B;
        line-height: 1.6;
        max-width: 480px;
        margin: 0 auto;
    }

    /* ── Instruction Card ── */
    .how-card {
        background: #FFFFFF;
        border: 1px solid #E0D5C7;
        border-radius: 12px;
        padding: 24px;
        margin: 24px 0;
        box-shadow: 0 2px 4px rgba(232, 93, 4, 0.08);
    }

    .how-card-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 16px;
    }

    .how-step {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 12px;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 15px;
        color: #1A1A1A;
        line-height: 1.5;
    }

    .step-num {
        background: #E85D04;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 13px;
        width: 24px;
        height: 24px;
        min-width: 24px;
        border-radius: 9999px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 1px;
    }

    /* ── Score Pill (top of game screen) ── */
    .score-pill {
        display: inline-flex;
        gap: 24px;
        background: #FFFFFF;
        border: 1px solid #E0D5C7;
        border-radius: 9999px;
        padding: 8px 24px;
        box-shadow: 0 2px 4px rgba(232, 93, 4, 0.08);
        font-family: 'Space Grotesk', sans-serif;
    }

    .pill-item {
        text-align: center;
    }

    .pill-value {
        font-size: 20px;
        font-weight: 700;
        color: #1A1A1A;
    }

    .pill-label {
        font-size: 11px;
        color: #6B6B6B;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* ── Video ── */
    .video-frame {
        border-radius: 12px;
        overflow: hidden;
        margin: 16px 0;
        background: #1A1A1A;
        border: 1px solid #E0D5C7;
        box-shadow: 0 4px 16px rgba(232, 93, 4, 0.12);
    }

    /* ── Question prompt ── */
    .question-prompt {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #1A1A1A;
        text-align: center;
        margin: 24px 0 16px 0;
        letter-spacing: -0.02em;
    }

    /* ── Result Cards ── */
    .reveal-card {
        background: #FFFFFF;
        border: 1px solid #E0D5C7;
        border-radius: 12px;
        padding: 16px 24px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(232, 93, 4, 0.08);
        font-family: 'Space Grotesk', sans-serif;
    }

    .reveal-label {
        font-size: 11px;
        font-weight: 600;
        color: #6B6B6B;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
    }

    .reveal-value {
        font-size: 18px;
        font-weight: 700;
        color: #1A1A1A;
    }

    .tag-correct {
        display: inline-block;
        background: #2D6A4F;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 9999px;
        margin-left: 8px;
    }

    .tag-wrong {
        display: inline-block;
        background: #D00000;
        color: #FFFFFF;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 9999px;
        margin-left: 8px;
    }

    /* ── Outcome banner ── */
    .outcome-banner {
        text-align: center;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #E85D04;
        padding: 16px;
        margin: 8px 0;
    }

    /* ── Game Over ── */
    .report-card {
        background: #FFFFFF;
        border: 1px solid #E0D5C7;
        border-radius: 12px;
        padding: 32px;
        margin: 24px 0;
        box-shadow: 0 4px 16px rgba(232, 93, 4, 0.12);
        font-family: 'Space Grotesk', sans-serif;
    }

    .report-title {
        font-size: 14px;
        font-weight: 600;
        color: #6B6B6B;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 24px;
        text-align: center;
    }

    .report-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #F0EBE3;
        font-size: 16px;
    }

    .report-row:last-of-type {
        border-bottom: none;
    }

    .report-label {
        color: #1A1A1A;
        font-weight: 400;
    }

    .report-value {
        font-weight: 700;
        color: #1A1A1A;
    }

    .big-score {
        text-align: center;
        margin-top: 32px;
        padding-top: 24px;
        border-top: 2px solid #E0D5C7;
    }

    .big-score-number {
        font-size: 56px;
        font-weight: 700;
        color: #E85D04;
        letter-spacing: -0.03em;
    }

    .big-score-label {
        font-size: 16px;
        color: #6B6B6B;
        margin-top: 4px;
    }

    /* ── Divider ── */
    .groovy-divider {
        height: 2px;
        background: #E0D5C7;
        margin: 24px 0;
        border: none;
    }

    /* ── Button overrides ── */
    .stButton > button {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 9999px !important;
        height: 48px !important;
        font-size: 15px !important;
        transition: transform 0.15s ease !important;
    }

    .stButton > button:hover {
        transform: scale(1.02) !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #E85D04 !important;
        border-color: #E85D04 !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 2px solid #E0D5C7 !important;
        color: #1A1A1A !important;
    }

    /* ── Expander override ── */
    div[data-testid="stExpander"] {
        border: 1px solid #E0D5C7;
        border-radius: 12px;
        background: #FFFFFF;
        font-family: 'Space Grotesk', sans-serif;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE SCREEN
# ============================================================

if not st.session_state.game_started and not st.session_state.game_over:

    st.markdown("""
<div class="hero">
<div class="hero-title">Verify<span class="hero-accent">It</span></div>
<div class="hero-subtitle">You vs the model. Real or AI — make the call.</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="how-card">
<div class="how-card-title">How it works</div>
<div class="how-step"><div class="step-num">1</div><div>Watch a short video clip. Pause anytime.</div></div>
<div class="how-step"><div class="step-num">2</div><div>Decide — is it <strong>AI-generated</strong> or <strong>Real</strong>?</div></div>
<div class="how-step"><div class="step-num">3</div><div>See how you compare against the AI model's prediction and the actual answer.</div></div>
<div class="how-step"><div class="step-num">4</div><div>Clips get harder as you improve. Play as long as you want.</div></div>
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Game", use_container_width=True, type="primary"):
            random.seed(time.time())
            st.session_state.game_started = True
            st.session_state.current_clip = get_next_clip()
            st.session_state.used_clips.append(
                st.session_state.current_clip["filename"]
            )
            st.rerun()


# ============================================================
# GAME OVER
# ============================================================

elif st.session_state.game_over:

    st.markdown("""
<div class="hero">
<div class="hero-title">Game <span class="hero-accent">Over</span></div>
</div>
""", unsafe_allow_html=True)

    total = len(st.session_state.history)
    correct = sum(1 for h in st.session_state.history if h["player_correct"])
    percentage = int(100 * correct / total) if total > 0 else 0

    player_beat_ai = sum(
        1 for h in st.session_state.history
        if h["player_correct"] and not h["model_correct"]
    )
    ai_beat_player = sum(
        1 for h in st.session_state.history
        if not h["player_correct"] and h["model_correct"]
    )
    both_right = sum(
        1 for h in st.session_state.history
        if h["player_correct"] and h["model_correct"]
    )
    both_wrong = sum(
        1 for h in st.session_state.history
        if not h["player_correct"] and not h["model_correct"]
    )

    report_html = f'<div class="report-card">'
    report_html += f'<div class="report-title">Your Report</div>'
    report_html += f'<div class="report-row"><span class="report-label">Clips played</span><span class="report-value">{total}</span></div>'
    report_html += f'<div class="report-row"><span class="report-label">You beat the AI</span><span class="report-value">{player_beat_ai}</span></div>'
    report_html += f'<div class="report-row"><span class="report-label">AI beat you</span><span class="report-value">{ai_beat_player}</span></div>'
    report_html += f'<div class="report-row"><span class="report-label">Both correct</span><span class="report-value">{both_right}</span></div>'
    report_html += f'<div class="report-row"><span class="report-label">Both wrong</span><span class="report-value">{both_wrong}</span></div>'
    report_html += f'<div class="big-score">'
    report_html += f'<div class="big-score-number">{percentage}% accuracy</div>'
    report_html += f'<div class="big-score-label">You guessed {correct} out of {total} correctly!</div>'
    report_html += f'</div></div>'
    st.markdown(report_html, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Play Again", use_container_width=True, type="primary"):
            reset_game()
            st.rerun()
    with col2:
        if st.button("Exit", use_container_width=True, type="secondary"):
            reset_game()
            st.rerun()


# ============================================================
# MAIN GAME
# ============================================================

else:
    clip = st.session_state.current_clip

    # ── Top bar ──
    bar_col, end_col = st.columns([3, 1])

    with bar_col:
        pill_html = f'<div class="score-pill">'
        pill_html += f'<div class="pill-item"><div class="pill-value">{st.session_state.clip_index + 1}</div><div class="pill-label">Clip</div></div>'
        pill_html += f'<div class="pill-item"><div class="pill-value">{st.session_state.score}</div><div class="pill-label">Score</div></div>'
        pill_html += f'</div>'
        st.markdown(pill_html, unsafe_allow_html=True)

    with end_col:
        st.markdown("<div style='padding-top: 4px;'></div>", unsafe_allow_html=True)
        if st.button("End Game", use_container_width=True, type="secondary"):
            st.session_state.game_over = True
            st.rerun()

    # ── Video (no thumbnail hiding — plays directly) ──
    embed_url = get_drive_embed_url(clip["video_url"])
    video_html = f'<div class="video-frame"><iframe src="{embed_url}" width="100%" height="480" frameborder="0" allowfullscreen></iframe></div>'
    st.markdown(video_html, unsafe_allow_html=True)

    # ── Answer buttons ──
    if not st.session_state.answered:

        st.markdown('<div class="question-prompt">AI or Real?</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Real", use_container_width=True, type="secondary"):
                st.session_state.player_guess = "real"
                st.session_state.answered = True
                st.session_state.score_updated = False
                st.rerun()

        with col2:
            if st.button("AI", use_container_width=True, type="primary"):
                st.session_state.player_guess = "ai"
                st.session_state.answered = True
                st.session_state.score_updated = False
                st.rerun()

    # ── Results ──
    else:
        guess = st.session_state.player_guess
        true_label = clip["true_label"]
        model_pred = clip["model_prediction"]
        model_conf = clip["model_confidence"]

        player_correct = (guess == true_label)
        model_correct = (model_pred == true_label)
        message, outcome = get_result_message(player_correct, model_correct)

        # Update score exactly once per clip
        if not st.session_state.score_updated:
            if player_correct:
                st.session_state.score += 1
            update_skill(player_correct)
            st.session_state.score_updated = True
            st.session_state.history.append({
                "filename": clip["filename"],
                "player_guess": guess,
                "true_label": true_label,
                "model_prediction": model_pred,
                "model_confidence": model_conf,
                "difficulty": clip["difficulty"],
                "player_correct": player_correct,
                "model_correct": model_correct,
                "result_message": message,
            })

        # Reveal 1: Player's answer
        p_tag = "tag-correct" if player_correct else "tag-wrong"
        p_text = "Correct" if player_correct else "Wrong"
        card1 = f'<div class="reveal-card"><div class="reveal-label">Your Answer</div><div class="reveal-value">{guess.upper()}<span class="{p_tag}">{p_text}</span></div></div>'
        st.markdown(card1, unsafe_allow_html=True)

        # Reveal 2: Model's prediction + confidence
        m_tag = "tag-correct" if model_correct else "tag-wrong"
        m_text = "Correct" if model_correct else "Wrong"
        card2 = f'<div class="reveal-card"><div class="reveal-label">AI Model — {model_conf:.1%} confident</div><div class="reveal-value">{model_pred.upper()}<span class="{m_tag}">{m_text}</span></div></div>'
        st.markdown(card2, unsafe_allow_html=True)

        # Reveal 3: Actual answer
        card3 = f'<div class="reveal-card"><div class="reveal-label">Actual Answer</div><div class="reveal-value">{true_label.upper()}</div></div>'
        st.markdown(card3, unsafe_allow_html=True)

        # Outcome
        st.markdown(f'<div class="outcome-banner">{message}</div>', unsafe_allow_html=True)

        # Next clip
        st.markdown('<div class="groovy-divider"></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Next Clip", use_container_width=True, type="primary"):
                st.session_state.clip_index += 1
                st.session_state.answered = False
                st.session_state.player_guess = None
                st.session_state.score_updated = False
                st.session_state.current_clip = get_next_clip()
                st.session_state.used_clips.append(
                    st.session_state.current_clip["filename"]
                )
                st.rerun()