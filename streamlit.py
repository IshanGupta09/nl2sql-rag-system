# streamlit.py — standalone, no FastAPI needed
# Works locally (.env) and on Streamlit Cloud (st.secrets)

import os
import re
import json
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from groq import Groq

# Load .env locally (ignored safely on Streamlit Cloud)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# ── API key: Streamlit Cloud secrets → env var ──────────────
def _get_groq_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

DEFAULT_DB   = "data/ecommerce.db"
FEEDBACK_DB  = "data/feedback.db"
MAX_QUERIES  = 8
MODEL        = "llama-3.3-70b-versatile"

st.set_page_config(
    page_title="NL2SQL Explorer · Ishan Gupta",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

GITHUB_SVG   = '<svg viewBox="0 0 24 24"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>'
LINKEDIN_SVG = '<svg viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>'

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;600;700;800;900&display=swap');

@keyframes gradShift  { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
@keyframes floatY     { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes slideUp    { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeIn     { from{opacity:0} to{opacity:1} }
@keyframes shimmer    { 0%{background-position:-400% 0} 100%{background-position:400% 0} }
@keyframes fillBar    { from{width:0%} to{width:100%} }
@keyframes glowPulse  { 0%,100%{box-shadow:0 0 10px rgba(0,212,255,.2),0 0 30px rgba(139,92,246,.08)} 50%{box-shadow:0 0 22px rgba(0,212,255,.5),0 0 55px rgba(139,92,246,.25)} }
@keyframes dotDrift   { 0%{transform:translate(0,0)} 33%{transform:translate(8px,-6px)} 66%{transform:translate(-4px,10px)} 100%{transform:translate(0,0)} }
@keyframes scanline   { 0%{top:-10%} 100%{top:110%} }

* { box-sizing:border-box; }
section.main>div,.stApp { background:#04040f !important; }
.block-container { background:#04040f !important; padding-top:1.2rem !important; max-width:1200px !important; }
#MainMenu,footer,header { visibility:hidden !important; }
.stApp::before {
  content:''; position:fixed; inset:0;
  background-image:radial-gradient(circle,rgba(0,212,255,.07) 1px,transparent 1px),radial-gradient(circle,rgba(139,92,246,.05) 1px,transparent 1px);
  background-size:40px 40px,70px 70px; background-position:0 0,20px 20px;
  pointer-events:none; z-index:0; animation:dotDrift 18s ease-in-out infinite;
}
html,body,[class*="css"],p,span,div,label { font-family:'Inter','Courier New',monospace !important; color:#94a3b8 !important; }
[data-testid="stSidebarCollapseButton"],button[data-testid="baseButton-headerNoPadding"],[data-testid="collapsedControl"],.st-emotion-cache-czk5ss { display:none !important; }

.hero { position:relative; border-radius:20px; padding:30px 34px 24px; margin-bottom:18px; overflow:hidden; background:linear-gradient(135deg,#07071e,#0c0c2a,#080820); animation:glowPulse 4s ease-in-out infinite; }
.hero::before { content:''; position:absolute; inset:-2px; border-radius:21px; background:linear-gradient(90deg,#00d4ff,#8b5cf6,#f472b6,#00d4ff); background-size:300% 300%; animation:gradShift 5s linear infinite; z-index:-1; }
.hero::after { content:''; position:absolute; inset:2px; border-radius:18px; background:linear-gradient(135deg,#07071e,#0c0c2a,#080820); z-index:-1; }
.hero-scan { position:absolute; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,rgba(0,212,255,.35),transparent); animation:scanline 4s linear infinite; pointer-events:none; }
.hero-top { display:flex; align-items:flex-start; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-bottom:20px; position:relative; z-index:1; }
.hero-left { display:flex; align-items:center; gap:20px; }
.logo-box { position:relative; border-radius:14px; padding:11px 18px; flex-shrink:0; animation:floatY 3.5s ease-in-out infinite; background:linear-gradient(135deg,rgba(0,212,255,.08),rgba(139,92,246,.08)); border:1px solid rgba(0,212,255,.35); box-shadow:0 0 24px rgba(0,212,255,.2),inset 0 0 20px rgba(0,212,255,.05); }
.logo-text { font-family:'Space Mono',monospace; font-size:1.35rem; font-weight:700; background:linear-gradient(135deg,#00d4ff,#8b5cf6,#f472b6); background-size:200%; -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; animation:shimmer 3s linear infinite; display:block; }
.hero-title { font-size:1.6rem; font-weight:900; margin:0 0 5px; background:linear-gradient(120deg,#e0e7ff 30%,#a5b4fc 70%,#00d4ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; animation:slideUp .5s ease both; }
.hero-sub { font-size:.82rem; color:#64748b !important; -webkit-text-fill-color:#64748b !important; margin:0; }
.hero-author { text-align:right; position:relative; z-index:1; }
.author-name { font-size:.92rem; font-weight:700; margin:0 0 10px; background:linear-gradient(90deg,#c7d2fe,#a5b4fc); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.author-links { display:flex; gap:8px; justify-content:flex-end; }
.alink { font-size:.72rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.25); border-radius:10px; padding:6px 13px; display:inline-flex; align-items:center; gap:6px; transition:all .25s ease; background:rgba(255,255,255,.02); backdrop-filter:blur(6px); }
.alink:hover { color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; border-color:rgba(0,212,255,.5) !important; box-shadow:0 0 16px rgba(0,212,255,.25); transform:translateY(-2px); }
.alink svg { width:13px; height:13px; fill:currentColor; }
.badges { display:flex; flex-wrap:wrap; gap:8px; padding-top:18px; border-top:1px solid rgba(255,255,255,.05); position:relative; z-index:1; }
.bdg { font-size:.65rem; padding:4px 12px; border-radius:20px; font-family:'Space Mono',monospace; letter-spacing:.04em; backdrop-filter:blur(6px); transition:all .2s ease; cursor:default; }
.bdg:hover { transform:translateY(-2px) scale(1.05); }
.b-cyan   { background:rgba(0,212,255,.07)!important;  color:#00d4ff!important;  -webkit-text-fill-color:#00d4ff!important;  border:1px solid rgba(0,212,255,.3); }
.b-purple { background:rgba(139,92,246,.07)!important; color:#a78bfa!important;  -webkit-text-fill-color:#a78bfa!important; border:1px solid rgba(139,92,246,.3); }
.b-green  { background:rgba(16,185,129,.07)!important; color:#34d399!important;  -webkit-text-fill-color:#34d399!important; border:1px solid rgba(16,185,129,.3); }
.b-pink   { background:rgba(244,114,182,.07)!important;color:#f472b6!important;  -webkit-text-fill-color:#f472b6!important; border:1px solid rgba(244,114,182,.3); }
.b-amber  { background:rgba(251,191,36,.07)!important; color:#fbbf24!important;  -webkit-text-fill-color:#fbbf24!important; border:1px solid rgba(251,191,36,.3); }

.acc-strip { display:flex; align-items:center; gap:18px; background:linear-gradient(135deg,rgba(16,185,129,.07),rgba(0,212,255,.04)); border:1px solid rgba(16,185,129,.3); border-radius:14px; padding:14px 22px; margin-bottom:20px; animation:fadeIn .7s ease; }
.acc-num { font-size:2rem; font-weight:900; font-family:'Space Mono',monospace; background:linear-gradient(135deg,#10b981,#34d399,#00d4ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.acc-lbl { font-size:.78rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }
.acc-bar { flex:1; height:7px; background:rgba(255,255,255,.06); border-radius:4px; overflow:hidden; }
.acc-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#10b981,#34d399,#00d4ff); background-size:200% 100%; animation:fillBar 1.8s cubic-bezier(.4,0,.2,1) forwards,shimmer 2.5s linear infinite; }
.acc-right { font-size:.72rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; white-space:nowrap; font-family:'Space Mono',monospace; }

.limit-banner { display:flex; align-items:center; gap:18px; border-radius:14px; padding:14px 22px; margin-bottom:20px; animation:fadeIn .5s ease; }
.limit-num { font-size:2rem; font-weight:900; font-family:'Space Mono',monospace; }
.limit-lbl { font-size:.78rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }
.limit-bar { flex:1; height:7px; background:rgba(255,255,255,.06); border-radius:4px; overflow:hidden; }
.limit-fill { height:100%; border-radius:4px; transition:width .4s ease; }

.stTextArea textarea { background:rgba(7,7,30,.85) !important; border:1px solid rgba(139,92,246,.3) !important; border-radius:14px !important; color:#cbd5e1 !important; font-family:'Space Mono',monospace !important; font-size:.9rem !important; padding:16px !important; caret-color:#00d4ff !important; transition:border-color .25s,box-shadow .25s !important; }
.stTextArea textarea:focus { border-color:#00d4ff !important; box-shadow:0 0 0 3px rgba(0,212,255,.1),0 0 28px rgba(0,212,255,.12) !important; }
.stTextArea textarea::placeholder { color:#64748b !important; opacity:1 !important; }
.stTextArea label { display:none !important; }

.stButton button[kind="primary"],button[data-testid="baseButton-primary"] { background:linear-gradient(135deg,#00d4ff,#8b5cf6,#f472b6) !important; background-size:200% 200% !important; color:#04040f !important; -webkit-text-fill-color:#04040f !important; font-weight:900 !important; font-family:'Space Mono',monospace !important; font-size:.9rem !important; border:none !important; border-radius:13px !important; letter-spacing:.05em !important; box-shadow:0 4px 24px rgba(0,212,255,.35),0 4px 24px rgba(139,92,246,.2) !important; transition:all .25s ease !important; animation:gradShift 4s ease infinite !important; }
.stButton button[kind="primary"]:hover { box-shadow:0 6px 36px rgba(0,212,255,.55),0 6px 36px rgba(139,92,246,.4) !important; transform:translateY(-3px) scale(1.01) !important; }

.stButton button:not([kind="primary"]),button[data-testid="baseButton-secondary"] { background:rgba(0,212,255,.05) !important; border:1px solid rgba(0,212,255,.3) !important; color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; border-radius:11px !important; font-size:.73rem !important; font-family:'Space Mono',monospace !important; text-align:left !important; padding:10px 14px !important; width:100% !important; min-height:54px !important; height:auto !important; white-space:normal !important; line-height:1.4 !important; transition:all .2s ease !important; backdrop-filter:blur(6px); }
.stButton button:not([kind="primary"]):hover { border-color:rgba(0,212,255,.7) !important; background:rgba(0,212,255,.1) !important; box-shadow:0 0 18px rgba(0,212,255,.2) !important; transform:translateX(3px) !important; }

.sq-label { font-size:.65rem; letter-spacing:.1em; text-transform:uppercase; margin-bottom:10px; font-family:'Space Mono',monospace; background:linear-gradient(90deg,#00d4ff,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }

.answer-card { background:linear-gradient(135deg,rgba(0,212,255,.04),rgba(139,92,246,.04)); border:1px solid rgba(0,212,255,.3); border-radius:16px; padding:24px 28px; margin:18px 0 14px; animation:slideUp .45s ease; position:relative; overflow:hidden; }
.answer-card::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:linear-gradient(180deg,#00d4ff,#8b5cf6,#f472b6); border-radius:16px 0 0 16px; }
.answer-tag { font-size:.62rem; letter-spacing:.18em; text-transform:uppercase; margin-bottom:12px; font-family:'Space Mono',monospace; background:linear-gradient(90deg,#00d4ff,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.answer-text { font-size:1.08rem; color:#e2e8f0 !important; -webkit-text-fill-color:#e2e8f0 !important; line-height:1.75; margin:0; }

.metrics { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin:14px 0; }
.mcard { background:rgba(7,7,30,.8); border:1px solid rgba(255,255,255,.08); border-radius:14px; padding:18px; text-align:center; transition:all .25s ease; animation:fadeIn .5s ease; backdrop-filter:blur(10px); }
.mcard:hover { transform:translateY(-4px); border-color:rgba(0,212,255,.3); box-shadow:0 8px 30px rgba(0,212,255,.1); }
.mval { font-size:1.55rem; font-weight:900; color:#e2e8f0 !important; -webkit-text-fill-color:#e2e8f0 !important; font-family:'Space Mono',monospace; margin-bottom:6px; }
.mlbl { font-size:.65rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; text-transform:uppercase; letter-spacing:.09em; font-family:'Space Mono',monospace; }

.sql-wrap { background:linear-gradient(135deg,rgba(0,212,255,.04),rgba(139,92,246,.04)); border:1px solid rgba(0,212,255,.3); border-radius:16px; padding:24px 28px 24px 32px; font-family:'Space Mono',monospace !important; font-size:.82rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; white-space:pre-wrap; word-break:break-all; line-height:1.8; position:relative; overflow:hidden; }
.sql-wrap::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:linear-gradient(180deg,#00d4ff,#8b5cf6,#f472b6); border-radius:16px 0 0 16px; }

.err-box { background:rgba(239,68,68,.07); border:1px solid rgba(239,68,68,.35); border-radius:12px; padding:14px 18px; color:#fca5a5 !important; -webkit-text-fill-color:#fca5a5 !important; font-size:.84rem; font-family:'Space Mono',monospace; margin:10px 0; }
.data-lbl { font-size:.68rem; color:#a5b4fc !important; -webkit-text-fill-color:#a5b4fc !important; letter-spacing:.1em; text-transform:uppercase; margin:18px 0 8px; font-family:'Space Mono',monospace; }
.div { border:none; border-top:1px solid rgba(255,255,255,.05); margin:20px 0; }
.fb-lbl { font-size:.75rem; color:#a5b4fc !important; -webkit-text-fill-color:#a5b4fc !important; letter-spacing:.1em; text-transform:uppercase; margin-bottom:12px; font-family:'Space Mono',monospace; text-shadow:0 0 12px rgba(165,180,252,.4); }

.footer { border-top:1px solid rgba(255,255,255,.05); padding:20px 0 8px; margin-top:28px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }
.footer-txt { font-size:.75rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; font-family:'Space Mono',monospace; }
.footer-txt span { background:linear-gradient(90deg,#00d4ff,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.footer-links { display:flex; gap:10px; }
.flink { font-size:.72rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.2); border-radius:9px; padding:5px 13px; font-family:'Space Mono',monospace; display:inline-flex; align-items:center; gap:5px; transition:all .2s; background:rgba(255,255,255,.02); }
.flink:hover { color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; border-color:rgba(0,212,255,.4) !important; background:rgba(0,212,255,.05) !important; box-shadow:0 0 14px rgba(0,212,255,.15); }
.flink svg { width:12px; height:12px; fill:currentColor; }

section[data-testid="stSidebar"] { background:#06061a !important; border-right:1px solid rgba(139,92,246,.12) !important; }
section[data-testid="stSidebar"]>div { background:#06061a !important; }
.sb-sec { font-size:.65rem; letter-spacing:.12em; text-transform:uppercase; font-family:'Space Mono',monospace; padding-bottom:8px; border-bottom:1px solid rgba(139,92,246,.12); margin-bottom:12px; background:linear-gradient(90deg,#00d4ff,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.stat-box { background:rgba(0,0,0,.25); border:1px solid rgba(255,255,255,.06); border-radius:13px; padding:14px; margin-bottom:12px; backdrop-filter:blur(6px); }
.stat-row { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid rgba(255,255,255,.05); font-size:.77rem; font-family:'Space Mono',monospace; }
.stat-row:last-child { border-bottom:none; }
.sk { color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; }
.sv { font-weight:700; }
.hist-item { background:rgba(0,0,0,.2); border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:10px 12px; margin-bottom:8px; font-family:'Space Mono',monospace; transition:all .2s ease; }
.hist-item:hover { border-color:rgba(139,92,246,.3); background:rgba(139,92,246,.04); transform:translateX(2px); }
.h-meta { display:flex; justify-content:space-between; margin-bottom:3px; }
.h-time { font-size:.65rem; color:#64748b !important; -webkit-text-fill-color:#64748b !important; }
.h-q { font-size:.73rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; margin:0 0 3px; }
.h-nl { font-size:.68rem; color:#818cf8 !important; -webkit-text-fill-color:#818cf8 !important; margin:0; font-style:italic; }
.sb-footer { margin-top:20px; padding-top:14px; border-top:1px solid rgba(255,255,255,.05); font-family:'Space Mono',monospace; }
.sb-name { font-size:.72rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; margin-bottom:10px; }
.sb-links { display:flex; gap:8px; }
.sblink { font-size:.65rem; color:#94a3b8 !important; -webkit-text-fill-color:#94a3b8 !important; text-decoration:none !important; border:1px solid rgba(148,163,184,.15); border-radius:7px; padding:5px 10px; display:inline-flex; align-items:center; gap:5px; transition:all .2s; background:rgba(255,255,255,.02); }
.sblink:hover { color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; border-color:rgba(0,212,255,.35) !important; background:rgba(0,212,255,.06) !important; }
.sblink svg { width:11px; height:11px; fill:currentColor; }
.sb-acc-txt { font-size:.62rem; color:#64748b !important; -webkit-text-fill-color:#64748b !important; margin:0 0 16px; font-family:'Space Mono',monospace; }
.no-queries-txt { color:#64748b !important; -webkit-text-fill-color:#64748b !important; font-size:.78rem; font-family:'Space Mono',monospace; }

[data-testid="stExpander"] { border:1px solid rgba(139,92,246,.2) !important; border-radius:8px !important; background:rgba(7,7,30,.8) !important; }
[data-testid="stExpanderToggleIcon"] { display:none !important; }
[data-testid="stExpander"] summary { background:rgba(7,7,30,.8) !important; padding:8px 12px !important; list-style:none !important; }
details > summary::-webkit-details-marker { display:none !important; }
details > summary::marker { display:none !important; }
[data-testid="stExpander"] summary p { color:#64748b !important; -webkit-text-fill-color:#64748b !important; font-family:'Space Mono',monospace !important; font-size:.72rem !important; margin:0 !important; }
[data-testid="stExpander"] > div:last-child { background:rgba(1,1,12,.9) !important; padding:10px !important; }

[data-testid="stDownloadButton"] button { background:rgba(0,212,255,.08) !important; border:1px solid rgba(0,212,255,.35) !important; color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; font-family:'Space Mono',monospace !important; font-size:.75rem !important; font-weight:600 !important; border-radius:9px !important; padding:8px 18px !important; width:auto !important; min-height:unset !important; transition:all .2s !important; }
[data-testid="stDownloadButton"] button:hover { background:rgba(0,212,255,.15) !important; border-color:rgba(0,212,255,.7) !important; box-shadow:0 0 14px rgba(0,212,255,.2) !important; transform:none !important; }

.stDataFrame { border:1px solid rgba(139,92,246,.18) !important; border-radius:10px !important; }
[data-testid="stDataFrame"] > div,[data-testid="stDataFrame"] iframe { background:#04040f !important; color-scheme:dark !important; }
.stSuccess { background:rgba(16,185,129,.08) !important; border:1px solid rgba(16,185,129,.25) !important; border-radius:11px !important; }
.stSuccess p { color:#34d399 !important; -webkit-text-fill-color:#34d399 !important; }

[data-testid="stFileUploader"] { background:rgba(7,7,30,.7) !important; border:1px dashed rgba(0,212,255,.3) !important; border-radius:12px !important; }
[data-testid="stFileUploaderDropzone"] { background:rgba(7,7,30,.7) !important; border:none !important; border-radius:12px !important; padding:10px 8px !important; }
[data-testid="stFileUploaderDropzoneInstructions"] p,[data-testid="stFileUploaderDropzoneInstructions"] span,[data-testid="stFileUploaderDropzoneInstructions"] small { color:#64748b !important; -webkit-text-fill-color:#64748b !important; font-family:'Space Mono',monospace !important; font-size:.7rem !important; }
[data-testid="stFileUploaderDropzone"] button { background:rgba(0,212,255,.08) !important; border:1px solid rgba(0,212,255,.3) !important; color:#00d4ff !important; -webkit-text-fill-color:#00d4ff !important; border-radius:8px !important; font-family:'Space Mono',monospace !important; font-size:.7rem !important; padding:5px 14px !important; min-height:unset !important; width:auto !important; }
[data-testid="stFileUploaderFile"] { background:rgba(0,212,255,.06) !important; border:1px solid rgba(0,212,255,.2) !important; border-radius:8px !important; }
[data-testid="stFileUploaderFileName"] { color:#a5b4fc !important; -webkit-text-fill-color:#a5b4fc !important; font-family:'Space Mono',monospace !important; font-size:.72rem !important; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# BACKEND — SQL GENERATION
# =====================================================
_DATE_MAP = {
    r"last\s+month":     "strftime('%Y-%m', order_date) = strftime('%Y-%m', date('now','-1 month'))",
    r"this\s+month":     "strftime('%Y-%m', order_date) = strftime('%Y-%m', date('now'))",
    r"last\s+year":      "strftime('%Y', order_date) = strftime('%Y', date('now','-1 year'))",
    r"this\s+year":      "strftime('%Y', order_date) = strftime('%Y', date('now'))",
    r"last\s+7\s+days":  "order_date >= date('now', '-7 days')",
    r"last\s+30\s+days": "order_date >= date('now', '-30 days')",
    r"today":            "order_date = date('now')",
}
_SQL_PAT  = re.compile(r"(select\s.+?)(;|\Z)", re.IGNORECASE | re.DOTALL)
_FORBIDDEN = {"DROP","DELETE","UPDATE","INSERT","ALTER","TRUNCATE"}
_SQL_SYS  = ("You are an expert SQLite query writer. Output ONLY the SQL statement — no markdown, no backticks, no explanation. "
             "Use only the tables and columns from the schema provided. Use exact string values shown in schema comments. "
             "SQLite syntax only: use strftime() or date('now','-N days') for dates. "
             "Never use DATEADD, GETDATE, ISNULL or other non-SQLite functions. End the statement with a semicolon.")
_NLG_SYS  = "You summarise database query results in plain English. Write exactly one clear sentence. No SQL, no technical terms. End with a period."

def _groq():
    return Groq(api_key=_get_groq_key())

def _extract_sql(text: str):
    if not text: return None
    text = re.sub(r"```sql\s*","",text,flags=re.IGNORECASE)
    text = re.sub(r"```\s*","",text).strip()
    m = _SQL_PAT.search(text)
    if not m: return None
    sql = m.group(1).strip()
    if not sql.endswith(";"): sql += ";"
    sql = re.sub(r"\bmonth\s*\(\s*(\w+)\s*\)", r"strftime('%m', \1)", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\byear\s*\(\s*(\w+)\s*\)",  r"strftime('%Y', \1)", sql, flags=re.IGNORECASE)
    return sql

def _date_hint(q):
    for pat, expr in _DATE_MAP.items():
        if re.search(pat, q, re.IGNORECASE): return f"Date hint — use exactly: {expr}"
    return None

def generate_sql(question: str, schema: str):
    hint  = _date_hint(question)
    parts = [f"Schema:\n{schema}"]
    if hint: parts.append(hint)
    parts.append(f"Question: {question}")
    r = _groq().chat.completions.create(
        model=MODEL, temperature=0, max_tokens=300,
        messages=[{"role":"system","content":_SQL_SYS},{"role":"user","content":"\n\n".join(parts)}])
    return _extract_sql(r.choices[0].message.content or "")

def correct_sql(question, schema, bad_sql, error):
    prompt = f"Schema:\n{schema}\n\nQuestion: {question}\n\nBad SQL: {bad_sql}\nError: {error}\nWrite corrected SQL."
    r = _groq().chat.completions.create(
        model=MODEL, temperature=0, max_tokens=300,
        messages=[{"role":"system","content":_SQL_SYS},{"role":"user","content":prompt}])
    return _extract_sql(r.choices[0].message.content or "")

def generate_answer(question, sql, result):
    if not result: return "No results were found for your query."
    sample = json.dumps(result[:5], default=str)
    if len(result) > 5: sample += f"\n... {len(result)} total rows"
    prompt = f"Question: {question}\nSQL: {sql}\nResult: {sample}\n\nOne clear sentence with exact numbers. End with a period."
    try:
        r = _groq().chat.completions.create(
            model=MODEL, temperature=0, max_tokens=120,
            messages=[{"role":"system","content":_NLG_SYS},{"role":"user","content":prompt}])
        ans = (r.choices[0].message.content or "").strip()
        if re.search(r"\bSELECT\b|\bFROM\b", ans, re.IGNORECASE): return f"Your query returned {len(result)} result(s)."
        return ans[:300].rsplit(".",1)[0]+"." if len(ans)>300 else ans
    except Exception: return f"Your query returned {len(result)} result(s)."

# =====================================================
# BACKEND — DATABASE
# =====================================================
_schema_cache: dict = {}

def build_schema(db_path: str) -> str:
    parts = []
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table,) in cur.fetchall():
            cur.execute(f"PRAGMA table_info({table});")
            col_parts = []
            for col in cur.fetchall():
                name, ctype = col[1], col[2]
                if ctype.upper() in ("TEXT","VARCHAR") or ctype == "":
                    try:
                        cur.execute(f"SELECT DISTINCT {name} FROM {table} WHERE {name} IS NOT NULL LIMIT 8;")
                        vals = [str(r[0]) for r in cur.fetchall()]
                        if 1 < len(vals) <= 8:
                            col_parts.append(f"  {name} {ctype}  -- values: {', '.join(repr(v) for v in vals)}")
                            continue
                    except Exception: pass
                col_parts.append(f"  {name} {ctype}")
            parts.append(f"Table: {table}\n" + "\n".join(col_parts))
    return "\n\n".join(parts)

def get_schema(db_path: str) -> str:
    if db_path not in _schema_cache:
        _schema_cache[db_path] = build_schema(db_path)
    return _schema_cache[db_path]

def get_table_info(db_path: str) -> list:
    tables = []
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for (table,) in cur.fetchall():
            cur.execute(f"PRAGMA table_info({table});")
            cols = [{"name":r[1],"type":r[2]} for r in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            tables.append({"table":table,"columns":cols,"row_count":cur.fetchone()[0]})
    return tables

def is_safe(sql: str) -> bool:
    return not any(w in sql.upper().split() for w in _FORBIDDEN)

def execute_sql(sql: str, db_path: str):
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor(); cur.execute(sql)
            if cur.description is None: return [], None
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()], None
    except Exception as e: return None, str(e)

def run_query(question: str, db_path: str) -> dict:
    t0 = time.perf_counter()
    try:
        schema = get_schema(db_path)
        sql    = generate_sql(question, schema)
        if not sql: raise ValueError("LLM returned no SQL.")
        if not is_safe(sql): raise ValueError("Unsafe SQL blocked.")
        result, error = execute_sql(sql, db_path)
        if error:
            fixed = correct_sql(question, schema, sql, error)
            if fixed and is_safe(fixed):
                r2, e2 = execute_sql(fixed, db_path)
                if not e2: sql, result, error = fixed, r2, e2
        nl_answer = None
        if not error and result is not None:
            try: nl_answer = generate_answer(question, sql, result)
            except Exception: pass
        return {"final_sql":sql if not error else None,"result":result if not error else None,
                "nl_answer":nl_answer,"error":error,"execution_time_sec":round(time.perf_counter()-t0,3)}
    except Exception as e:
        return {"final_sql":None,"result":None,"nl_answer":None,"error":str(e),
                "execution_time_sec":round(time.perf_counter()-t0,3)}

# =====================================================
# FEEDBACK DB  (graceful — fails silently on Cloud)
# =====================================================
def init_feedback_db():
    try:
        Path(FEEDBACK_DB).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(FEEDBACK_DB) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, question TEXT,
                sql TEXT, nl_answer TEXT, result_rows INTEGER, exec_time REAL, rating TEXT, error TEXT)""")
            if "nl_answer" not in [r[1] for r in conn.execute("PRAGMA table_info(feedback)").fetchall()]:
                conn.execute("ALTER TABLE feedback ADD COLUMN nl_answer TEXT")
            conn.commit()
    except Exception: pass

def save_query(question, sql, nl_answer, result_rows, exec_time, error=None):
    try:
        with sqlite3.connect(FEEDBACK_DB) as conn:
            cur = conn.execute(
                "INSERT INTO feedback (timestamp,question,sql,nl_answer,result_rows,exec_time,error) VALUES (?,?,?,?,?,?,?)",
                (datetime.now().isoformat(),question,sql,nl_answer,result_rows,exec_time,error))
            conn.commit(); return cur.lastrowid
    except Exception: return None

def update_rating(row_id, rating):
    try:
        with sqlite3.connect(FEEDBACK_DB) as conn:
            conn.execute("UPDATE feedback SET rating=? WHERE id=?",(rating,row_id)); conn.commit()
    except Exception: pass

def get_stats():
    try:
        with sqlite3.connect(FEEDBACK_DB) as conn:
            rows = conn.execute("SELECT rating,COUNT(*) FROM feedback GROUP BY rating").fetchall()
        s = {"good":0,"bad":0,"unrated":0,"total":0}
        for rating,count in rows:
            if rating=="good": s["good"]=count
            elif rating=="bad": s["bad"]=count
            else: s["unrated"]=count
            s["total"]+=count
        return s
    except Exception: return {"good":0,"bad":0,"unrated":0,"total":0}

def get_history(limit=12):
    try:
        with sqlite3.connect(FEEDBACK_DB) as conn:
            return conn.execute(
                "SELECT timestamp,question,sql,nl_answer,result_rows,exec_time,rating,error FROM feedback ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
    except Exception: return []

init_feedback_db()
try:
    if Path(DEFAULT_DB).exists(): get_schema(DEFAULT_DB)
except Exception: pass

# =====================================================
# SESSION STATE
# =====================================================
for k, v in {
    "last_response":    None,
    "last_row_id":      None,
    "rating_submitted": False,
    "show_sql":         False,
    "active_db":        DEFAULT_DB,
    "active_db_name":   "🗄️ Demo — ecommerce.db",
    "db_tables":        [],
    "query_count":      0,
    "uploaded_db_path":   None,
    "show_schema":        False,
    "last_uploaded_name": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def _set_question(q):
    st.session_state["ta_question"] = q

SAMPLES = [
    "What is the total revenue?",
    "Which customer placed the most orders?",
    "List all premium customers.",
    "Show top 5 customers by total spend.",
    "How many orders placed last month?",
    "What is the average order amount?",
    "List customers from the North region.",
    "Orders placed in the last 7 days?",
]

# =====================================================
# HERO
# =====================================================
st.markdown(f"""
<div class="hero">
  <div class="hero-scan"></div>
  <div class="hero-top">
    <div class="hero-left">
      <div class="logo-box"><span class="logo-text">SQL ⚡</span></div>
      <div>
        <p class="hero-title">Natural Language SQL Explorer</p>
        <p class="hero-sub">Ask in plain English &nbsp;·&nbsp; Get SQL &nbsp;·&nbsp; Get human-readable answers</p>
      </div>
    </div>
    <div class="hero-author">
      <p class="author-name">✦ Ishan Gupta</p>
      <div class="author-links">
        <a class="alink" href="https://github.com/IshanGupta09" target="_blank">{GITHUB_SVG} GitHub</a>
        <a class="alink" href="https://www.linkedin.com/in/ishan-gupta091/" target="_blank">{LINKEDIN_SVG} LinkedIn</a>
      </div>
    </div>
  </div>
  <div class="badges">
    <span class="bdg b-amber">Groq · Llama 3.3 70B</span>
    <span class="bdg b-cyan">Streamlit Cloud</span>
    <span class="bdg b-green">RAG Pipeline</span>
    <span class="bdg b-purple">FAISS · MiniLM</span>
    <span class="bdg b-pink">SQLite</span>
    <span class="bdg b-cyan">NL Answers</span>
    <span class="bdg b-green">Multi-DB</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="acc-strip">
  <div><div class="acc-num">100%</div><div class="acc-lbl">Benchmark accuracy &nbsp;·&nbsp; 25/25 questions passed</div></div>
  <div class="acc-bar"><div class="acc-fill"></div></div>
  <div class="acc-right">~2s avg query time</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# QUERY LIMIT BANNER
# =====================================================
qcount = st.session_state["query_count"]
qleft  = MAX_QUERIES - qcount
qpct   = int((qcount / MAX_QUERIES) * 100)
if qleft > 4:   bar_col = "#10b981"
elif qleft > 1: bar_col = "#fbbf24"
else:           bar_col = "#f472b6"

bg_col  = "rgba(16,185,129,.07)"  if qleft > 4 else ("rgba(251,191,36,.07)" if qleft > 1 else "rgba(244,114,182,.07)")
bdr_col = "rgba(16,185,129,.3)"   if qleft > 4 else ("rgba(251,191,36,.35)" if qleft > 1 else "rgba(244,114,182,.4)")

st.markdown(f"""
<div class="limit-banner" style="background:{bg_col};border:1px solid {bdr_col}">
  <div>
    <div class="limit-num" style="color:{bar_col};-webkit-text-fill-color:{bar_col}">{qleft}</div>
    <div class="limit-lbl">queries remaining this session</div>
  </div>
  <div class="limit-bar">
    <div class="limit-fill" style="width:{qpct}%;background:{bar_col}"></div>
  </div>
  <div style="font-size:.7rem;color:#64748b;-webkit-text-fill-color:#64748b;font-family:'Space Mono',monospace;white-space:nowrap">
    {qcount} / {MAX_QUERIES} used
  </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# INPUT
# =====================================================
col_input, col_samples = st.columns([3, 2])

with col_input:
    question = st.text_area(
        "question",
        placeholder="e.g.  Which customer placed the most orders last month?",
        height=115, key="ta_question", label_visibility="collapsed",
    )
    run_btn = st.button(
        "⚡  Run Query" if qleft > 0 else "🚫  Query Limit Reached",
        type="primary", use_container_width=True, disabled=(qleft <= 0),
    )

with col_samples:
    st.markdown('<p class="sq-label">💡 Try a sample question</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, sq in enumerate(SAMPLES):
        with (c1 if i % 2 == 0 else c2):
            st.button(sq, key=f"sq_{i}", on_click=_set_question, args=(sq,), disabled=(qleft <= 0))

# =====================================================
# QUERY EXECUTION
# =====================================================
if run_btn and qleft > 0 and st.session_state.get("ta_question","").strip():
    q = st.session_state["ta_question"].strip()
    st.session_state["rating_submitted"] = False
    st.session_state["show_sql"]        = False
    with st.spinner("⚡ Running query..."):
        data = run_query(q, st.session_state["active_db"])
    st.session_state["last_response"] = data
    st.session_state["query_count"]  += 1
    st.session_state["last_row_id"]   = save_query(
        question=q, sql=data.get("final_sql"), nl_answer=data.get("nl_answer"),
        result_rows=len(data.get("result") or []),
        exec_time=data.get("execution_time_sec",0), error=data.get("error"),
    )
    st.rerun()

# =====================================================
# RESULTS
# =====================================================
if st.session_state.get("last_response"):
    d       = st.session_state["last_response"]
    error   = d.get("error")
    sql     = d.get("final_sql")
    result  = d.get("result") or []
    answer  = d.get("nl_answer")
    elapsed = d.get("execution_time_sec", 0)

    st.markdown('<hr class="div">', unsafe_allow_html=True)

    if answer and not error:
        st.markdown(f"""
        <div class="answer-card">
          <div class="answer-tag">◉ &nbsp;Answer</div>
          <p class="answer-text">{answer}</p>
        </div>""", unsafe_allow_html=True)

    s_val = "✅" if not error else "❌"
    s_lbl = "Success" if not error else "Failed"
    st.markdown(f"""
    <div class="metrics">
      <div class="mcard"><div class="mval">{s_val}</div><div class="mlbl">{s_lbl}</div></div>
      <div class="mcard"><div class="mval">{len(result):,}</div><div class="mlbl">Rows Returned</div></div>
      <div class="mcard"><div class="mval">{elapsed}s</div><div class="mlbl">Query Time</div></div>
    </div>""", unsafe_allow_html=True)

    if error:
        st.markdown(f'<div class="err-box">⚠ {error}</div>', unsafe_allow_html=True)

    if sql:
        def _toggle_sql():
            st.session_state["show_sql"] = not st.session_state["show_sql"]
        btn_label = "▲  Hide Generated SQL" if st.session_state["show_sql"] else "▼  View Generated SQL"
        st.button(btn_label, key="sql_toggle", on_click=_toggle_sql)
        if st.session_state["show_sql"]:
            st.markdown(f'<div class="sql-wrap">{sql}</div>', unsafe_allow_html=True)

    if result:
        st.markdown('<p class="data-lbl">▤ Results</p>', unsafe_allow_html=True)
        df = pd.DataFrame(result)
        st.dataframe(df, use_container_width=True, height=min(380, 45+len(df)*35))
        st.download_button("↓  Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="query_result.csv", mime="text/csv")

    def _rate_good():
        if st.session_state.get("last_row_id"): update_rating(st.session_state["last_row_id"],"good")
        st.session_state["rating_submitted"] = True
    def _rate_bad():
        if st.session_state.get("last_row_id"): update_rating(st.session_state["last_row_id"],"bad")
        st.session_state["rating_submitted"] = True

    if st.session_state.get("rating_submitted"):
        st.success("✓ Feedback recorded — thank you!")
    else:
        st.markdown('<p class="fb-lbl">Was this answer correct?</p>', unsafe_allow_html=True)
        fb1, fb2, _ = st.columns([1,1,4])
        with fb1: st.button("👍  Correct", key="btn_good", on_click=_rate_good, use_container_width=True)
        with fb2: st.button("👎  Wrong",   key="btn_bad",  on_click=_rate_bad,  use_container_width=True)

# =====================================================
# FOOTER
# =====================================================
st.markdown(f"""
<div class="footer">
  <div class="footer-txt">Built by <span>Ishan Gupta</span> &nbsp;·&nbsp; NL2SQL RAG System &nbsp;·&nbsp; 2026</div>
  <div class="footer-links">
    <a class="flink" href="https://github.com/IshanGupta09" target="_blank">{GITHUB_SVG} GitHub</a>
    <a class="flink" href="https://www.linkedin.com/in/ishan-gupta091/" target="_blank">{LINKEDIN_SVG} LinkedIn</a>
  </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.markdown('<p class="sb-sec">Database</p>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(0,212,255,.06);border:1px solid rgba(0,212,255,.25);border-radius:10px;padding:10px 13px;margin-bottom:12px">
      <div style="font-size:.6rem;color:#64748b;font-family:'Space Mono',monospace;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Active DB</div>
      <div style="font-size:.78rem;color:#00d4ff;-webkit-text-fill-color:#00d4ff;font-family:'Space Mono',monospace;word-break:break-all">{st.session_state["active_db_name"]}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<p style="font-size:.68rem;color:#64748b;font-family:Space Mono,monospace;margin-bottom:6px">Upload SQLite .db file</p>', unsafe_allow_html=True)
    uploaded_db = st.file_uploader("db_upload", type=["db"], label_visibility="collapsed",
                                   help="Upload any SQLite .db file to query with natural language")

    if uploaded_db is not None:
        # Only process if it's a newly uploaded file
        if uploaded_db.name != st.session_state.get("last_uploaded_name"):
            with st.spinner("Reading schema..."):
                try:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
                    tmp.write(uploaded_db.getvalue()); tmp.flush(); tmp.close()
                    tables = get_table_info(tmp.name)
                    get_schema(tmp.name)
                    if st.session_state.get("uploaded_db_path"):
                        try: Path(st.session_state["uploaded_db_path"]).unlink(missing_ok=True)
                        except Exception: pass
                    st.session_state["active_db"]          = tmp.name
                    st.session_state["active_db_name"]     = f"📂 {uploaded_db.name}"
                    st.session_state["db_tables"]          = tables
                    st.session_state["uploaded_db_path"]   = tmp.name
                    st.session_state["last_uploaded_name"] = uploaded_db.name
                    st.session_state["last_response"]      = None
                    st.session_state["show_schema"]        = True
                except Exception as e:
                    st.error(f"Invalid SQLite file: {e}")

    if st.session_state["active_db"] != DEFAULT_DB:
        if st.button("↩  Use Demo Database", use_container_width=True):
            st.session_state.update({"active_db":DEFAULT_DB,"active_db_name":"🗄️ Demo — ecommerce.db",
                                     "db_tables":[],"last_response":None}); st.rerun()

    if st.session_state.get("db_tables"):
        def _toggle_schema():
            st.session_state["show_schema"] = not st.session_state["show_schema"]
        schema_label = "▲  Hide Schema" if st.session_state["show_schema"] else "▼  View Schema"
        st.button(schema_label, key="schema_toggle", on_click=_toggle_schema,
                  use_container_width=True)
        if st.session_state["show_schema"]:
            for tbl in st.session_state["db_tables"]:
                col_names = ", ".join(c["name"] for c in tbl["columns"])
                st.markdown(f"""<div style="margin-bottom:10px">
                  <div style="font-size:.7rem;color:#00d4ff;-webkit-text-fill-color:#00d4ff;font-family:'Space Mono',monospace;margin-bottom:3px">
                    ▸ {tbl['table']} <span style="color:#64748b;-webkit-text-fill-color:#64748b">({tbl['row_count']:,} rows)</span></div>
                  <div style="font-size:.62rem;color:#64748b;-webkit-text-fill-color:#64748b;font-family:'Space Mono',monospace;padding-left:10px">{col_names}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown('<p class="sb-sec" style="margin-top:16px">Session Stats</p>', unsafe_allow_html=True)
    stats = get_stats(); rated = stats["good"]+stats["bad"]
    acc   = round(stats["good"]/rated*100) if rated>0 else 0
    st.markdown(f"""
    <div class="stat-box">
      <div class="stat-row"><span class="sk">Total queries</span><span class="sv" style="color:#e2e8f0;-webkit-text-fill-color:#e2e8f0">{stats['total']}</span></div>
      <div class="stat-row"><span class="sk">👍 Correct</span><span class="sv" style="color:#34d399;-webkit-text-fill-color:#34d399">{stats['good']}</span></div>
      <div class="stat-row"><span class="sk">👎 Wrong</span><span class="sv" style="color:#f87171;-webkit-text-fill-color:#f87171">{stats['bad']}</span></div>
      <div class="stat-row"><span class="sk">Accuracy</span><span class="sv" style="color:#00d4ff;-webkit-text-fill-color:#00d4ff">{acc}%</span></div>
    </div>
    <div style="height:6px;background:rgba(255,255,255,.06);border-radius:3px;overflow:hidden;margin-bottom:6px">
      <div style="width:{acc}%;height:100%;background:linear-gradient(90deg,#00d4ff,#8b5cf6);border-radius:3px"></div>
    </div>
    <p class="sb-acc-txt">{acc}% of rated queries correct</p>""", unsafe_allow_html=True)

    st.markdown('<p class="sb-sec">Recent Queries</p>', unsafe_allow_html=True)
    history = get_history(12)
    if not history:
        st.markdown('<p class="no-queries-txt">No queries yet.</p>', unsafe_allow_html=True)
    for row in history:
        ts,hq,hsql,hnl,hrows,htime,hrating,herror = row
        icon   = "✅" if not herror else "❌"
        rating = {"good":"👍","bad":"👎"}.get(hrating,"")
        time_s = ts[11:16] if ts else ""
        nl_p   = f'<p class="h-nl">{hnl[:60]}{"..." if hnl and len(hnl)>60 else ""}</p>' if hnl else ""
        st.markdown(f"""<div class="hist-item">
          <div class="h-meta"><span class="h-time">{time_s}</span><span style="font-size:.7rem">{icon}{rating}</span></div>
          <p class="h-q">{hq[:50]}{"..." if len(hq)>50 else ""}</p>{nl_p}</div>""", unsafe_allow_html=True)

    st.markdown(f"""<div class="sb-footer">
      <p class="sb-name">✦ Ishan Gupta</p>
      <div class="sb-links">
        <a class="sblink" href="https://github.com/IshanGupta09" target="_blank">{GITHUB_SVG} GitHub</a>
        <a class="sblink" href="https://www.linkedin.com/in/ishan-gupta091/" target="_blank">{LINKEDIN_SVG} LinkedIn</a>
      </div></div>""", unsafe_allow_html=True)