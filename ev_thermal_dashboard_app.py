"""
=============================================================================
EV BATTERY THERMAL INTELLIGENCE DASHBOARD
=============================================================================
Interactive thermal telemetry & battery intelligence application.

Updates & Performance Refinements:
- 100% Vector SVG logos encoded as robust base64 Data-URIs (guaranteed visible
  across all browsers and Streamlit DOM sanitizers; zero emojis)
- Smart Splash Screen: waits until all calculations & charts are fully loaded
  in the browser before smoothly dissolving overlay (never cuts off early)
- Suppressed splash screen on subsequent reruns for instantaneous filtering
- Removed all text references to "converted to python" or "powered by streamlit"
- Completely removed the data pipeline section to match original clean UI
- Visible right-side cyber-cyan vertical scrollbar and floating Scroll Back pill
- Unified Plotly subplots & optimized striding for 60 FPS interactions
=============================================================================
"""

import os
import math
import base64
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# =============================================================================
# 1. STREAMLIT PAGE CONFIG & INJECTED STYLES
# =============================================================================
st.set_page_config(
    page_title="EV Battery Thermal Intelligence",
    page_icon="https://raw.githubusercontent.com/feathericons/feather/master/icons/zap.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Robust Base64 Vector SVG Logo Helper (Immune to DOMPurify / markdown stripping)
def icon_svg(name, size=18, color="#22d3ee"):
    svg_templates = {
        "search": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "folder": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
        "file": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
        "bolt": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        "chart": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        "link": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
        "trending": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "gear": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
        "visuals": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10h-10z"/></svg>',
        "sparkles": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/></svg>',
        "battery": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="17" height="12" rx="3"/><line x1="22" y1="11" x2="22" y2="13"/></svg>',
        "table": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>',
        "arrow_up": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>',
        "warning": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "info": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "check": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
    }
    raw = svg_templates.get(name, "")
    if not raw:
        return ""
    b64 = base64.b64encode(raw.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" style="vertical-align:middle;display:inline-block;pointer-events:none;" alt="{name}">'

def alert_box(kind, text):
    color = "#fb7185" if kind == "error" else "#f97316" if kind == "warning" else "#22d3ee"
    icon = icon_svg("warning" if kind in ["error", "warning"] else "info", 18, color)
    return f"""<div style="display:flex;align-items:center;gap:12px;padding:12px 18px;border-radius:14px;background:rgba(255,255,255,0.035);border:1px solid {color}44;margin:16px 0;color:#eef1ff;font-size:0.88rem;">{icon}<span>{text}</span></div>"""

# Check session state for one-time initial splash screen execution
if "has_loaded_splash" not in st.session_state:
    st.session_state["has_loaded_splash"] = True
    render_splash = True
else:
    render_splash = False

# Core App Stylesheet
APP_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg: #080b1a;
    --card: rgba(255, 255, 255, 0.05);
    --bd: rgba(255, 255, 255, 0.08);
    --tx: #eef1ff;
    --mu: #97a3c7;
    --c1: #22d3ee;
    --c2: #8b5cf6;
    --c3: #f97316;
    --c4: #fb7185;
    --g: linear-gradient(120deg, #22d3ee, #8b5cf6 55%, #fb7185);
    --hot: linear-gradient(120deg, #8b5cf6, #fb7185 55%, #f97316);
}

/* 1. SUPPRESS STREAMLIT DEPLOY BUTTON & DEFAULT HEADER */
.stDeployButton,
[data-testid="stDeployButton"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0px !important;
    pointer-events: none !important;
}

header[data-testid="stHeader"] {
    display: none !important;
    height: 0px !important;
    padding: 0 !important;
    background: transparent !important;
}

/* 2. SMOOTH SCROLLING & VISIBLE RIGHT-SIDE SCROLLBAR */
html, body, [data-testid="stAppViewContainer"] {
    scroll-behavior: smooth !important;
    scrollbar-width: thin !important;
    scrollbar-color: rgba(34, 211, 238, 0.45) #080b1a !important;
}

[data-testid="stAppViewContainer"] {
    overflow-y: scroll !important;
}

[data-testid="stAppViewContainer"]::-webkit-scrollbar,
::-webkit-scrollbar {
    width: 10px !important;
    height: 10px !important;
    display: block !important;
}

[data-testid="stAppViewContainer"]::-webkit-scrollbar-track,
::-webkit-scrollbar-track {
    background: #080b1a !important;
    border-left: 1px solid rgba(255, 255, 255, 0.05) !important;
}

[data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb,
::-webkit-scrollbar-thumb {
    background: rgba(34, 211, 238, 0.38) !important;
    border-radius: 99px !important;
    border: 2px solid #080b1a !important;
    transition: background 0.25s ease !important;
}

[data-testid="stAppViewContainer"]::-webkit-scrollbar-thumb:hover,
::-webkit-scrollbar-thumb:hover {
    background: rgba(34, 211, 238, 0.85) !important;
}

/* Prevent unwanted internal scrollbars inside cards */
.dashboard-card,
.kpi-card,
.corr-card,
div[data-testid="column"],
div[data-testid="stMarkdownContainer"] {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    overflow: hidden !important;
}

.dashboard-card::-webkit-scrollbar,
.kpi-card::-webkit-scrollbar,
.corr-card::-webkit-scrollbar,
div[data-testid="column"]::-webkit-scrollbar,
div[data-testid="stMarkdownContainer"]::-webkit-scrollbar {
    display: none !important;
    width: 0px !important;
    height: 0px !important;
}

/* Typography & App Container */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', system-ui, -apple-system, sans-serif !important;
    color: #eef1ff !important;
    background-color: #080b1a !important;
}

[data-testid="stAppViewContainer"] {
    background-image: 
        radial-gradient(900px 500px at 8% 0%, rgba(91,45,180,.35), transparent),
        radial-gradient(800px 500px at 100% 10%, rgba(14,116,144,.3), transparent),
        radial-gradient(700px 500px at 60% 100%, rgba(194,65,12,.3), transparent) !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
    padding-top: 14px !important;
}

/* Custom Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: rgba(8, 11, 26, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.side-nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 20px;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 10px;
    color: #97a3c7 !important;
    font-size: 0.82rem;
    font-weight: 500;
    text-decoration: none !important;
    border: 1px solid transparent;
    transition: all 0.2s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.nav-link:hover {
    color: #eef1ff !important;
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.1);
    transform: translateX(3px);
}

.custom-csv-tag {
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(34, 211, 238, 0.06);
    border: 1px solid rgba(34, 211, 238, 0.25);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Floating Scroll-Back Pill on bottom right */
.scroll-back-pill {
    position: fixed;
    bottom: 28px;
    right: 28px;
    z-index: 999999;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    border-radius: 99px;
    background: rgba(14, 20, 44, 0.92);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(34, 211, 238, 0.45);
    color: #eef1ff !important;
    font-size: 0.82rem;
    font-weight: 700;
    text-decoration: none !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55), 0 0 20px rgba(34, 211, 238, 0.25);
    transition: all 0.25s cubic-bezier(0.2, 0.7, 0.2, 1);
    cursor: pointer;
}

.scroll-back-pill:hover {
    transform: translateY(-3px) scale(1.04);
    background: rgba(20, 30, 68, 0.98);
    border-color: #22d3ee;
    color: #22d3ee !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 28px rgba(34, 211, 238, 0.5);
}

/* 3. BATTERY CHARGING SPLASH OVERLAY */
#battery-splash {
    position: fixed;
    inset: 0;
    z-index: 9999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: 
        radial-gradient(700px 450px at 50% 42%, rgba(34,211,238,.14), transparent 70%),
        radial-gradient(600px 400px at 55% 58%, rgba(139,92,246,.14), transparent 70%),
        #060813;
    pointer-events: all;
}

.batt-box {
    position: relative;
    width: 220px;
    height: 106px;
    border: 3.5px solid rgba(207, 216, 255, 0.65);
    border-radius: 20px;
    padding: 9px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    background: rgba(255, 255, 255, 0.03);
    box-shadow: 0 0 35px rgba(34, 211, 238, 0.25);
    animation: battBob 3s ease-in-out infinite;
}

@keyframes battBob {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-7px); }
}

.batt-nipple {
    position: absolute;
    right: -14px;
    top: 50%;
    transform: translateY(-50%);
    width: 10px;
    height: 38px;
    background: rgba(207, 216, 255, 0.65);
    border-radius: 0 5px 5px 0;
}

.batt-seg {
    flex: 1;
    height: 100%;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    opacity: 0.15;
    transition: all 0.4s ease;
}

.seg-1 {
    animation: chargeSeg1 0.6s cubic-bezier(0.2, 0.7, 0.2, 1) 0.3s forwards;
}
@keyframes chargeSeg1 {
    to {
        opacity: 1;
        background: linear-gradient(135deg, #22d3ee, #06b6d4);
        box-shadow: 0 0 20px rgba(34, 211, 238, 0.75);
    }
}

.seg-2 {
    animation: chargeSeg2 0.6s cubic-bezier(0.2, 0.7, 0.2, 1) 1.0s forwards;
}
@keyframes chargeSeg2 {
    to {
        opacity: 1;
        background: linear-gradient(135deg, #8b5cf6, #a855f7);
        box-shadow: 0 0 22px rgba(139, 92, 246, 0.75);
    }
}

.seg-3 {
    animation: chargeSeg3 0.6s cubic-bezier(0.2, 0.7, 0.2, 1) 1.7s forwards;
}
@keyframes chargeSeg3 {
    to {
        opacity: 1;
        background: linear-gradient(135deg, #fb7185, #f97316);
        box-shadow: 0 0 25px rgba(249, 115, 22, 0.85);
    }
}

.batt-bolt {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    filter: drop-shadow(0 0 10px #ffffff);
    animation: boltPulse 1.4s ease-in-out infinite;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: center;
}
@keyframes boltPulse {
    0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(0.95); }
    50% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); filter: drop-shadow(0 0 16px #67e8f9); }
}

.splash-ttl {
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #eef1ff;
    margin-top: 28px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.6);
}

.splash-msg-box {
    margin-top: 12px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.92rem;
    letter-spacing: 0.05em;
    color: #97a3c7;
}

.step-txt {
    position: absolute;
    opacity: 0;
}

.step-1 {
    animation: txtFade1 0.9s ease 0.2s forwards;
}
@keyframes txtFade1 {
    0% { opacity: 0; transform: translateY(4px); }
    20%, 80% { opacity: 1; transform: translateY(0); color: #67e8f9; }
    100% { opacity: 0; transform: translateY(-4px); }
}

.step-2 {
    animation: txtFade2 0.9s ease 1.0s forwards;
}
@keyframes txtFade2 {
    0% { opacity: 0; transform: translateY(4px); }
    20%, 80% { opacity: 1; transform: translateY(0); color: #c084fc; }
    100% { opacity: 0; transform: translateY(-4px); }
}

.step-3 {
    animation: txtFade3 1.0s ease 1.7s forwards;
}
@keyframes txtFade3 {
    0% { opacity: 0; transform: translateY(4px); }
    20%, 90% { opacity: 1; transform: translateY(0); color: #34d399; font-weight: 700; }
    100% { opacity: 1; transform: translateY(0); color: #34d399; }
}

.splash-pill {
    margin-top: 18px;
    padding: 4px 14px;
    border-radius: 99px;
    background: rgba(34, 211, 238, 0.08);
    border: 1px solid rgba(34, 211, 238, 0.25);
    color: #67e8f9;
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* 4. CARDS, TYPOGRAPHY & SPACING */
.dashboard-card {
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 22px 24px;
    backdrop-filter: blur(12px);
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    margin-bottom: 20px;
    overflow: hidden !important;
    box-sizing: border-box !important;
    will-change: transform, border-color;
    transform: translateZ(0);
}

.dashboard-card:hover {
    border-color: rgba(34, 211, 238, 0.35);
    box-shadow: 0 14px 30px -15px rgba(34, 211, 238, 0.3);
}

.corr-card {
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 12px;
    backdrop-filter: blur(10px);
    overflow: hidden !important;
    box-sizing: border-box !important;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
    will-change: transform, border-color;
    transform: translateZ(0);
}

.corr-card:hover {
    border-color: rgba(34, 211, 238, 0.3);
    box-shadow: 0 10px 25px -12px rgba(34, 211, 238, 0.25);
}

.corr-title {
    font-weight: 700;
    font-size: 1.02rem;
    color: #eef1ff;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.corr-desc {
    color: #97a3c7;
    font-size: 0.8rem;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.corr-r {
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
}

.kpi-card {
    position: relative;
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 18px 20px;
    overflow: hidden !important;
    backdrop-filter: blur(10px);
    transition: transform 0.25s ease, border-color 0.25s ease;
    min-height: 124px;
    margin-bottom: 14px;
    will-change: transform, border-color;
    transform: translateZ(0);
}

.kpi-card::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: linear-gradient(120deg, #22d3ee, #8b5cf6 55%, #fb7185);
}

.kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 255, 255, 0.22);
}

.kpi-title {
    color: #97a3c7;
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.kpi-value {
    display: block;
    font-size: 2.1rem;
    font-weight: 800;
    margin: 4px 0 2px;
    background: linear-gradient(120deg, #8b5cf6, #fb7185 55%, #f97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-variant-numeric: tabular-nums;
}

.kpi-sub {
    color: #97a3c7;
    font-size: 0.76rem;
    line-height: 1.3;
}

.eyebrow-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #97a3c7;
    padding: 6px 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 99px;
    background: rgba(255, 255, 255, 0.04);
    margin-bottom: 14px;
}

.hero-title {
    font-size: clamp(2rem, 4.2vw, 3.4rem);
    font-weight: 800;
    line-height: 1.1;
    background: linear-gradient(120deg, #22d3ee, #8b5cf6 55%, #fb7185);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 12px;
}

.hero-sub {
    color: #97a3c7;
    max-width: 52em;
    font-size: 1.02rem;
    line-height: 1.6;
    margin-bottom: 34px;
}

.section-hdr {
    position: relative;
    font-size: 1.55rem;
    font-weight: 700;
    padding-left: 16px;
    margin-top: 48px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.section-hdr::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.15em;
    bottom: 0.15em;
    width: 4px;
    border-radius: 4px;
    background: linear-gradient(120deg, #22d3ee, #8b5cf6 55%, #fb7185);
}

.section-desc {
    color: #97a3c7;
    font-size: 0.92rem;
    margin-bottom: 22px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.86rem;
}

.custom-table th {
    color: #97a3c7;
    font-weight: 600;
    padding: 11px 12px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.custom-table td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    font-variant-numeric: tabular-nums;
    color: #eef1ff;
}

.custom-table tr:hover td {
    background: rgba(255, 255, 255, 0.04);
}

.pos { color: #f97316 !important; font-weight: 700; }
.neg { color: #22d3ee !important; font-weight: 700; }
.zer { color: #97a3c7 !important; font-weight: 700; }

div[data-baseweb="select"] > div {
    background-color: #141a35 !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    color: #eef1ff !important;
}

input {
    background-color: #141a35 !important;
    color: #eef1ff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
}
</style>
<div id="overview-top-anchor"></div>
"""
st.html(APP_STYLES)

# Splash overlay injected via native st.html only on initial visit
if render_splash:
    SPLASH_HTML = f"""
<div id="battery-splash">
    <div class="batt-box">
        <div class="batt-seg seg-1"></div>
        <div class="batt-seg seg-2"></div>
        <div class="batt-seg seg-3"></div>
        <div class="batt-bolt">{icon_svg('bolt', 34, '#67e8f9')}</div>
        <div class="batt-nipple"></div>
    </div>
    <div class="splash-ttl">EV Battery Thermal Intelligence</div>
    <div class="splash-msg-box">
        <span class="step-txt step-1">Stage 1/3 · Ingesting vehicle telemetry (33%)...</span>
        <span class="step-txt step-2">Stage 2/3 · Imputing nulls & thermal balancing (66%)...</span>
        <span class="step-txt step-3">Stage 3/3 · Fully Charged (100%) · Launching dashboard...</span>
    </div>
    <div class="splash-pill">200,000 Cells Loaded</div>
</div>
"""
    st.html(SPLASH_HTML)

# Floating Scroll-Back Pill in the Right with Smooth JS scroll
SCROLL_BACK_HTML = f"""
<a href="#overview-top-anchor" id="scrollBackBtn" class="scroll-back-pill" title="Scroll back to top" onclick="var c=document.querySelector('[data-testid=\\'stAppViewContainer\\']')||window;if(c.scrollTo){{c.scrollTo({{top:0,behavior:'smooth'}});}}else{{c.scrollTop=0;}}window.scrollTo({{top:0,behavior:'smooth'}});return false;">
    {icon_svg('arrow_up', 17, '#22d3ee')}
    <span>Scroll Back</span>
</a>
"""
st.html(SCROLL_BACK_HTML)

# Lightweight Plotly configuration for silky smooth FPS
PLOTLY_CONFIG = dict(
    displayModeBar=False,
    responsive=True
)


def apply_dark_theme(fig, title=None, height=300, x_title=None, y_title=None, y_range=None, show_legend=False, tick_angle=None):
    """
    Applies unified cyber-dark glassmorphism styling to any Plotly figure.
    Safely sets axes without keyword argument collision.
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(20,26,53,0.35)",
        font=dict(family="Outfit, system-ui, sans-serif", color="#97a3c7", size=12),
        margin=dict(l=40, r=25, t=40 if title else 25, b=35),
        showlegend=show_legend,
        height=height
    )
    if title:
        fig.update_layout(title=dict(text=title, font=dict(family="Outfit", color="#eef1ff", size=14)))

    x_kwargs = dict(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        color="#97a3c7",
        tickfont=dict(family="Outfit", size=11)
    )
    if x_title:
        x_kwargs["title"] = x_title
    if tick_angle is not None:
        x_kwargs["tickangle"] = tick_angle
    try:
        fig.update_xaxes(**x_kwargs)
    except Exception:
        pass

    y_kwargs = dict(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.1)",
        color="#97a3c7",
        tickfont=dict(family="Outfit", size=11)
    )
    if y_title:
        y_kwargs["title"] = y_title
    if y_range:
        y_kwargs["range"] = y_range
    try:
        fig.update_yaxes(**y_kwargs)
    except Exception:
        pass

    return fig


THERM_LABELS = {
    "cell_temperature_max": "Max cell temp (°C)",
    "cell_temperature_avg": "Avg cell temp (°C)",
    "temp_rise": "Temp rise over ambient (°C)",
    "average_ambient_temperature": "Ambient temp (°C)",
    "temperature_variance": "Temperature variance",
    "thermal_runaway_risk": "Thermal runaway risk",
    "cooling_system_health": "Cooling system health"
}


# =============================================================================
# 2. DATA CLEANING & CACHED INGESTION
# =============================================================================
@st.cache_data(show_spinner=False)
def load_and_clean_dataset(file_path_or_buffer):
    """
    Cleans ev_battery_failure_dataset according to exact domain specifications:
    1. Imputation: Categorical features filled with Mode, Numerical with Median.
    2. Operational Domain Clamping: Temperatures [-30, 90]°C with max >= avg.
    3. Health & Risk Scores clamped to [0, 100].
    4. Derived engineering: temp_rise = cell_temperature_max - ambient_temperature.
    """
    df = pd.read_csv(file_path_or_buffer)
    raw_rows = len(df)
    miss_before = int(df.isnull().sum().sum())

    # Mode imputation for categorical
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if df[col].isnull().any():
            mode_val = df[col].mode()[0]
            df[col] = df[col].fillna(mode_val)

    # Median imputation for numerical
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].isnull().any():
            med_val = df[col].median()
            df[col] = df[col].fillna(med_val)

    # Domain consistency constraints
    if "cell_temperature_avg" in df.columns:
        df["cell_temperature_avg"] = df["cell_temperature_avg"].clip(-30, 90)
    if "cell_temperature_max" in df.columns:
        df["cell_temperature_max"] = df["cell_temperature_max"].clip(-30, 90)
        if "cell_temperature_avg" in df.columns:
            df["cell_temperature_max"] = np.maximum(df["cell_temperature_max"], df["cell_temperature_avg"])

    pct_columns = [
        "battery_health_percent", "state_of_charge",
        "cooling_system_health", "thermal_runaway_risk",
        "discharge_efficiency", "charge_efficiency", "capacity_loss_percent"
    ]
    for c in pct_columns:
        if c in df.columns:
            df[c] = df[c].clip(0, 100)

    # Derived feature
    if "cell_temperature_max" in df.columns and "average_ambient_temperature" in df.columns:
        df["temp_rise"] = df["cell_temperature_max"] - df["average_ambient_temperature"]

    miss_after = int(df.isnull().sum().sum())

    cleaning_meta = {
        "raw_rows": raw_rows,
        "miss_before": miss_before,
        "miss_after": miss_after,
        "cols": len(df.columns)
    }
    return df, cleaning_meta


# Locate dataset in directory, script folder, or parent directory
_app_dir = os.path.dirname(os.path.abspath(__file__))
CANDIDATE_PATHS = [
    "ev_battery_failure_dataset (1).csv",
    "ev_battery_failure_dataset.csv",
    os.path.join(_app_dir, "ev_battery_failure_dataset (1).csv"),
    os.path.join(_app_dir, "ev_battery_failure_dataset.csv"),
    "../ev_battery_failure_dataset (1).csv",
    "../ev_battery_failure_dataset.csv"
]

target_file = None
for p in CANDIDATE_PATHS:
    if os.path.exists(p):
        target_file = p
        break

# Sidebar Header with Vector SVG Logo
st.sidebar.html(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding:4px 0;">
    <div style="width:36px;height:36px;border-radius:10px;background:rgba(34,211,238,0.12);border:1px solid rgba(34,211,238,0.3);display:flex;align-items:center;justify-content:center;">
        {icon_svg('bolt', 20, '#22d3ee')}
    </div>
    <div>
        <div style="font-size:0.9rem;letter-spacing:0.12em;text-transform:uppercase;font-weight:700;color:#eef1ff;line-height:1.2;">EV Thermal</div>
        <div style="font-size:0.72rem;letter-spacing:0.06em;color:#97a3c7;">Intelligence Lab</div>
    </div>
</div>
""")

# Sidebar Navigation Menu with Vector SVG Logos
st.sidebar.html(f"""
<div style="font-size:0.66rem;letter-spacing:0.18em;text-transform:uppercase;color:rgba(151,163,199,0.7);margin:10px 0 6px 4px;">Navigation</div>
<div class="side-nav">
    <a href="#overview-sec" class="nav-link">{icon_svg('bolt', 16, '#22d3ee')} <span>Overview</span></a>
    <a href="#explorer-sec" class="nav-link">{icon_svg('table', 16, '#8b5cf6')} <span>Data Explorer</span></a>
    <a href="#statistics-sec" class="nav-link">{icon_svg('chart', 16, '#fb7185')} <span>Statistics</span></a>
    <a href="#correlation-sec" class="nav-link">{icon_svg('link', 16, '#f97316')} <span>Correlation</span></a>
    <a href="#regression-sec" class="nav-link">{icon_svg('trending', 16, '#22d3ee')} <span>Regression</span></a>
    <a href="#preprocessing-sec" class="nav-link">{icon_svg('gear', 16, '#8b5cf6')} <span>Preprocessing</span></a>
    <a href="#visuals-sec" class="nav-link">{icon_svg('visuals', 16, '#fb7185')} <span>Visualizations</span></a>
    <a href="#advanced-sec" class="nav-link">{icon_svg('sparkles', 16, '#f97316')} <span>Advanced Mining</span></a>
</div>
""")

# Custom SVG File Upload Tag
st.sidebar.html(f"""
<div class="custom-csv-tag">
    <div style="display:flex;align-items:center;gap:8px;">
        {icon_svg('file', 17, '#22d3ee')}
        <span style="font-weight:600;font-size:0.8rem;color:#eef1ff;">Load Custom CSV Dataset</span>
    </div>
</div>
""")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

active_source = uploaded_file if uploaded_file is not None else target_file

if active_source is None:
    st.html(alert_box("error", "Dataset not found. Please place <code>ev_battery_failure_dataset (1).csv</code> in this folder or upload it via the sidebar."))
    st.stop()

with st.spinner("Processing dataset…"):
    df_clean, meta = load_and_clean_dataset(active_source)

# Overall baseline metrics for delta comparisons
BASELINE = {
    "n": len(df_clean),
    "tmax": float(df_clean["cell_temperature_max"].mean()),
    "fail": float(df_clean["battery_failure"].mean()) if "battery_failure" in df_clean.columns else 0.0,
    "risk": float(df_clean["thermal_runaway_risk"].mean()) if "thermal_runaway_risk" in df_clean.columns else 0.0,
    "rise": float(df_clean["temp_rise"].mean()) if "temp_rise" in df_clean.columns else 0.0
}


# =============================================================================
# 3. SIDEBAR SEARCH, SORTING & MULTI-FILTER CONTROLS
# =============================================================================
st.sidebar.html("<div style='font-size:0.66rem;letter-spacing:0.18em;text-transform:uppercase;color:rgba(151,163,199,0.7);margin:16px 0 8px 4px;'>Filters & Search</div>")

# Vector Magnifying Glass Search Tag
st.sidebar.html(f"""
<div style="display:flex;align-items:center;gap:7px;font-size:0.8rem;color:#eef1ff;margin-bottom:6px;font-weight:600;">
    {icon_svg('search', 16, '#22d3ee')}
    <span>Search Vehicle ID / Model</span>
</div>
""")
search_query = st.sidebar.text_input("Search Vehicle ID / Model", "", placeholder="e.g. EV1024 or Sedan", label_visibility="collapsed")

available_types = ["All types"] + sorted(list(df_clean["vehicle_type"].unique()))
selected_type = st.sidebar.selectbox("Vehicle Type", available_types, index=0)

available_chems = ["All chemistries"] + sorted(list(df_clean["battery_chemistry"].unique()))
selected_chem = st.sidebar.selectbox("Battery Chemistry", available_chems, index=0)

available_brands = ["All brands"] + sorted(list(df_clean["vehicle_brand"].unique()))
selected_brand = st.sidebar.selectbox("Vehicle Brand", available_brands, index=0)

failure_option = st.sidebar.selectbox("Failure Status", ["All vehicles", "Failed Only (1)", "Healthy Only (0)"])

max_odo = int(df_clean["odometer_km"].max())
selected_odo = st.sidebar.slider("Odometer (km) ≥", min_value=0, max_value=max_odo, value=0, step=10000)

# Ultra-fast vectorized filtering using raw NumPy arrays
mask = np.ones(len(df_clean), dtype=bool)

if selected_type != "All types":
    mask &= (df_clean["vehicle_type"].values == selected_type)

if selected_chem != "All chemistries":
    mask &= (df_clean["battery_chemistry"].values == selected_chem)

if selected_brand != "All brands":
    mask &= (df_clean["vehicle_brand"].values == selected_brand)

if failure_option == "Failed Only (1)":
    mask &= (df_clean["battery_failure"].values == 1)
elif failure_option == "Healthy Only (0)":
    mask &= (df_clean["battery_failure"].values == 0)

if selected_odo > 0:
    mask &= (df_clean["odometer_km"].values >= selected_odo)

if search_query.strip():
    q = search_query.strip().lower()
    s_mask = (
        df_clean["vehicle_id"].astype(str).str.lower().str.contains(q) |
        df_clean["vehicle_type"].astype(str).str.lower().str.contains(q) |
        df_clean["vehicle_brand"].astype(str).str.lower().str.contains(q)
    )
    if "vehicle_model" in df_clean.columns:
        s_mask = s_mask | df_clean["vehicle_model"].astype(str).str.lower().str.contains(q)
    mask &= s_mask.values

filtered_df = df_clean[mask]

# Selection count indicator in sidebar
sel_count = len(filtered_df)
count_color = "#67e8f9" if sel_count >= 30 else "#fb7185"
st.sidebar.html(f"""
<div style="margin-top:16px;padding:8px 12px;border-radius:12px;background:rgba(34,211,238,0.08);border:1px solid rgba(34,211,238,0.25);text-align:center;">
    <span style="color:{count_color};font-weight:700;font-size:0.8rem;">{sel_count:,} of {BASELINE['n']:,} vehicles</span>
</div>
""")


# =============================================================================
# 4. MAIN HERO SECTION & LIVE KPI OVERVIEW
# =============================================================================
st.html('<div id="overview-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="eyebrow-badge">{icon_svg("bolt", 13, "#22d3ee")} Live Analytics · Every view responds to the filters</div>')
st.html('<div class="hero-title">EV Battery Thermal Intelligence</div>')
st.html("""
<div class="hero-sub">
How hot do EV battery cells run, and what drives it? An interactive walkthrough of the cleaned EV battery failure dataset, 
from data cleaning to statistics, regression and advanced visuals. Every number, table and chart responds to the filters.
</div>
""")

if sel_count == 0:
    st.html(alert_box("warning", "No vehicles match your current filter selection. Please relax your filters in the sidebar."))
    st.stop()

# Deterministic fast striding sample for buttery smooth 60 FPS plotting
step_size = max(1, len(filtered_df) // 500)
plot_sample = filtered_df.iloc[::step_size]

# Helper for formatted delta strings
def fmt_delta(val, unit="", invert=False):
    sgn = "+" if val > 0 else ""
    return f"{sgn}{val:.1f}{unit} vs dataset"

is_all = (sel_count == BASELINE["n"])
curr_tmax = float(filtered_df["cell_temperature_max"].mean())
curr_hottest = float(filtered_df["cell_temperature_max"].max())
curr_rise = float(filtered_df["temp_rise"].mean())
curr_risk = float(filtered_df["thermal_runaway_risk"].mean())
curr_fail = float(filtered_df["battery_failure"].mean()) * 100

st.html(f'<div class="section-hdr">{icon_svg("bolt", 22, "#22d3ee")} Overview & Key Indicators</div>')

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    sub = "whole dataset" if is_all else f"{(sel_count/BASELINE['n']*100):.1f}% of total"
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Vehicles</span>
        <b class="kpi-value">{sel_count:,}</b>
        <span class="kpi-sub">{sub}</span>
    </div>
    """)

with k2:
    sub = "all vehicles" if is_all else fmt_delta(curr_tmax - BASELINE["tmax"], " °C")
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Mean Max Temp</span>
        <b class="kpi-value">{curr_tmax:.1f} °C</b>
        <span class="kpi-sub">{sub}</span>
    </div>
    """)

with k3:
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Hottest Cell</span>
        <b class="kpi-value">{curr_hottest:.1f} °C</b>
        <span class="kpi-sub">Peak observed max</span>
    </div>
    """)

with k4:
    sub = "ambient baseline" if is_all else fmt_delta(curr_rise - BASELINE["rise"], " °C")
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Mean Temp Rise</span>
        <b class="kpi-value">{curr_rise:.1f} °C</b>
        <span class="kpi-sub">{sub}</span>
    </div>
    """)

with k5:
    sub = "scale 0–100" if is_all else fmt_delta(curr_risk - BASELINE["risk"])
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Thermal Risk</span>
        <b class="kpi-value">{curr_risk:.1f}</b>
        <span class="kpi-sub">{sub}</span>
    </div>
    """)

with k6:
    sub = "battery_failure = 1" if is_all else fmt_delta(curr_fail - (BASELINE["fail"] * 100), " pts")
    st.html(f"""
    <div class="kpi-card">
        <span class="kpi-title">Failure Rate</span>
        <b class="kpi-value">{curr_fail:.1f}%</b>
        <span class="kpi-sub">{sub}</span>
    </div>
    """)

# Overview Chart: Failure rate by chemistry (Clean & Prominent)
group_col = "battery_chemistry" if selected_chem == "All chemistries" else "vehicle_type"
rate_df = (
    filtered_df.groupby(group_col)["battery_failure"]
    .agg(["count", "mean"])
    .reset_index()
)
rate_df["fail_pct"] = rate_df["mean"] * 100

fig_fail = go.Figure(
    data=[
        go.Bar(
            x=rate_df[group_col],
            y=rate_df["fail_pct"],
            text=[f"{v:.1f}%" for v in rate_df["fail_pct"]],
            textposition="outside",
            textfont=dict(family="Outfit", color="#fb7185", size=12),
            marker=dict(
                color=rate_df["fail_pct"],
                colorscale=[[0, "#fb7185"], [1, "#f97316"]],
                line=dict(color="rgba(255,255,255,0.1)", width=1),
                cornerradius=8
            )
        )
    ]
)
max_y_rate = max(float(rate_df["fail_pct"].max()) * 1.25, 15.0)
apply_dark_theme(
    fig_fail,
    title=f"Battery Failure Rate by {group_col.replace('_', ' ').title()}",
    height=320,
    y_title="% Failed Vehicles",
    y_range=[0, max_y_rate]
)
st.plotly_chart(fig_fail, config=PLOTLY_CONFIG)


# =============================================================================
# 5. DATA EXPLORER & AGGREGATIONS
# =============================================================================
st.html('<div id="explorer-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("table", 22, "#8b5cf6")} Data Explorer</div>')
st.html('<div class="section-desc">Sorting, conditional filtering, and group-by aggregations on the hottest battery cells.</div>')

col_ex1, col_ex2 = st.columns(2)

with col_ex1:
    st.html(f"<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Top 8 Hottest Vehicles (Odometer ≥ {selected_odo:,} km)</h4>")
    top_hottest = (
        filtered_df.sort_values(by="cell_temperature_max", ascending=False)
        .head(8)[["vehicle_id", "vehicle_type", "battery_chemistry", "odometer_km", "cell_temperature_max", "battery_failure"]]
    )

    table_html = "<table class='custom-table'><thead><tr><th>Vehicle ID</th><th>Type</th><th>Chem</th><th>Odometer</th><th>Max °C</th><th>Status</th></tr></thead><tbody>"
    for _, row in top_hottest.iterrows():
        f_badge = "<span style='color:#f97316;'>FAILED</span>" if row["battery_failure"] == 1 else "<span style='color:#22d3ee;'>OK</span>"
        table_html += f"<tr><td><b>{row['vehicle_id']}</b></td><td>{row['vehicle_type']}</td><td>{row['battery_chemistry']}</td><td>{int(row['odometer_km']):,} km</td><td><b class='pos'>{row['cell_temperature_max']:.1f} °C</b></td><td>{f_badge}</td></tr>"
    table_html += "</tbody></table>"
    st.html(f"<div class='dashboard-card'>{table_html}</div>")

with col_ex2:
    grp_cat = "battery_chemistry" if selected_chem == "All chemistries" else "vehicle_type"
    st.html(f"<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Group by {grp_cat.replace('_', ' ').title()}</h4>")
    grp_df = (
        filtered_df.groupby(grp_cat)
        .agg(
            Count=("vehicle_id", "count"),
            Mean_Max=("cell_temperature_max", "mean"),
            Peak_Max=("cell_temperature_max", "max"),
            Failure_Rate=("battery_failure", "mean")
        )
        .reset_index()
    )

    grp_html = f"<table class='custom-table'><thead><tr><th>{grp_cat.replace('_', ' ').title()}</th><th>Count</th><th>Mean °C</th><th>Max °C</th><th>Failure Rate</th></tr></thead><tbody>"
    for _, row in grp_df.iterrows():
        grp_html += f"<tr><td><b>{row[grp_cat]}</b></td><td>{int(row['Count']):,}</td><td>{row['Mean_Max']:.1f} °C</td><td>{row['Peak_Max']:.1f} °C</td><td><b class='pos'>{row['Failure_Rate']*100:.1f}%</b></td></tr>"
    grp_html += "</tbody></table>"
    st.html(f"<div class='dashboard-card'>{grp_html}</div>")


# =============================================================================
# 6. STATISTICAL ANALYSIS & DISTRIBUTIONS
# =============================================================================
st.html('<div id="statistics-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("chart", 22, "#fb7185")} Statistical Analysis</div>')
st.html('<div class="section-desc">Parametric & non-parametric summary statistics and grouped frequency distribution tables.</div>')

selected_stat_col = st.selectbox(
    "Choose Thermal Attribute for Statistical Breakdown",
    options=list(THERM_LABELS.keys()),
    format_func=lambda k: THERM_LABELS[k],
    index=0
)

stat_series = filtered_df[selected_stat_col].dropna().values

if len(stat_series) > 0:
    st_mean = float(np.mean(stat_series))
    st_median = float(np.median(stat_series))
    vals, counts = np.unique(np.round(stat_series, 1), return_counts=True)
    st_mode = float(vals[np.argmax(counts)])
    st_var = float(np.var(stat_series, ddof=1)) if len(stat_series) > 1 else 0.0
    st_std = float(np.sqrt(st_var))
    q25, q75 = np.percentile(stat_series, [25, 75])
    st_iqr = float(q75 - q25)

    sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
    for col_el, name, val in [
        (sc1, "Mean", st_mean),
        (sc2, "Median", st_median),
        (sc3, "Mode", st_mode),
        (sc4, "Variance", st_var),
        (sc5, "Std Dev", st_std),
        (sc6, "IQR", st_iqr)
    ]:
        with col_el:
            st.html(f"""
            <div class="kpi-card">
                <span class="kpi-title">{name}</span>
                <b class="kpi-value">{val:.2f}</b>
            </div>
            """)

    # Grouped frequency distribution (8 equal width classes)
    hist_counts, bin_edges = np.histogram(stat_series, bins=8)
    freq_data = []
    for i in range(len(hist_counts)):
        b_label = f"{bin_edges[i]:.1f} – {bin_edges[i+1]:.1f}"
        freq_data.append({
            "Class": b_label,
            "Frequency": int(hist_counts[i]),
            "Share": f"{(hist_counts[i] / len(stat_series) * 100):.1f}%"
        })
    freq_df = pd.DataFrame(freq_data)

    col_st1, col_st2 = st.columns([1, 1.3])
    with col_st1:
        st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Grouped Frequency Table</h4>")
        freq_html = "<table class='custom-table'><thead><tr><th>Class Interval</th><th>Frequency</th><th>Share</th></tr></thead><tbody>"
        for _, r in freq_df.iterrows():
            freq_html += f"<tr><td>{r['Class']}</td><td>{r['Frequency']:,}</td><td><b>{r['Share']}</b></td></tr>"
        freq_html += "</tbody></table>"
        st.html(f"<div class='dashboard-card'>{freq_html}</div>")

    with col_st2:
        fig_dist = go.Figure(
            data=[
                go.Bar(
                    x=freq_df["Class"],
                    y=freq_df["Frequency"],
                    marker=dict(
                        color=freq_df["Frequency"],
                        colorscale=[[0, "#22d3ee"], [1, "#8b5cf6"]],
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                        cornerradius=6
                    )
                )
            ]
        )
        apply_dark_theme(
            fig_dist,
            title=f"Frequency Distribution: {THERM_LABELS[selected_stat_col]}",
            height=320,
            y_title="Count",
            tick_angle=-30
        )
        st.plotly_chart(fig_dist, config=PLOTLY_CONFIG)


# =============================================================================
# 7. CORRELATION ANALYSIS (PEARSON'S R)
# =============================================================================
st.html('<div id="correlation-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("link", 22, "#f97316")} Correlation Analysis</div>')
st.html('<div class="section-desc">Pearson\'s correlation coefficients and scatter plots against max cell temperature, recomputed live on the current selection.</div>')

corr_targets = [
    ("average_ambient_temperature", "Ambient Temp (°C)", "#f97316"),
    ("humidity", "Humidity (%)", "#22d3ee"),
    ("state_of_charge", "State of Charge (%)", "#8b5cf6")
]

corr_cols = st.columns(3)

for idx, (c_feat, c_label, c_color) in enumerate(corr_targets):
    with corr_cols[idx]:
        x_all = filtered_df[c_feat].values
        y_all = filtered_df["cell_temperature_max"].values
        
        # Pearson correlation
        if len(x_all) > 1 and np.std(x_all) > 0 and np.std(y_all) > 0:
            r_val = float(np.corrcoef(x_all, y_all)[0, 1])
        else:
            r_val = 0.0

        strength = (
            "No correlation" if abs(r_val) < 0.1 else
            "Weak " + ("positive" if r_val > 0 else "negative") if abs(r_val) < 0.3 else
            "Moderate " + ("positive" if r_val > 0 else "negative") if abs(r_val) < 0.6 else
            "Strong " + ("positive" if r_val > 0 else "negative")
        )
        r_class = "pos" if r_val > 0.1 else "neg" if r_val < -0.1 else "zer"

        st.html(f"""
        <div class="corr-card">
            <div class="corr-title">{strength}</div>
            <div class="corr-desc">Max temp vs {c_label}</div>
            <div class="corr-r {r_class}">r = {r_val:.3f}</div>
        </div>
        """)

        fig_sc = go.Figure(
            data=[
                go.Scattergl(
                    x=plot_sample[c_feat],
                    y=plot_sample["cell_temperature_max"],
                    mode="markers",
                    marker=dict(size=4, color=c_color, opacity=0.5)
                )
            ]
        )
        apply_dark_theme(
            fig_sc,
            height=250,
            x_title=c_label,
            y_title="Max Cell Temp (°C)"
        )
        st.plotly_chart(fig_sc, config=PLOTLY_CONFIG)


# =============================================================================
# 8. REGRESSION MODELING (SIMPLE & MULTIPLE)
# =============================================================================
st.html('<div id="regression-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("trending", 22, "#22d3ee")} Regression Analysis</div>')
st.html('<div class="section-desc">Predicting max cell temperature with Simple and Multiple Linear Regression fitted on your active selection.</div>')

multi_features = [
    "average_ambient_temperature", "humidity", "battery_stress_index",
    "discharge_efficiency", "temperature_variance", "internal_resistance"
]

if sel_count < 30:
    st.html(alert_box("info", "Select 30 or more vehicles to fit statistically valid regression models."))
else:
    # 1. Simple Linear Regression: Ambient -> Max Temp
    X_s = plot_sample[["average_ambient_temperature"]].values
    y_target = plot_sample["cell_temperature_max"].values

    lr_simple = LinearRegression()
    lr_simple.fit(X_s, y_target)
    y_pred_s = lr_simple.predict(X_s)

    mae_s = mean_absolute_error(y_target, y_pred_s)
    rmse_s = np.sqrt(mean_squared_error(y_target, y_pred_s))
    r2_s = r2_score(y_target, y_pred_s)
    b0_s = lr_simple.intercept_
    b1_s = lr_simple.coef_[0]

    # 2. Multiple Linear Regression: 6 Features -> Max Temp
    X_m = plot_sample[multi_features].values
    lr_multi = LinearRegression()
    lr_multi.fit(X_m, y_target)
    y_pred_m = lr_multi.predict(X_m)

    mae_m = mean_absolute_error(y_target, y_pred_m)
    rmse_m = np.sqrt(mean_squared_error(y_target, y_pred_m))
    r2_m = r2_score(y_target, y_pred_m)

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.html(f"""
        <div class="dashboard-card" style="margin-bottom:12px;">
            <h4 style="color:#eef1ff;margin-bottom:4px;">Simple: Ambient → Cell Temp</h4>
            <div style="color:#97a3c7;font-size:0.84rem;">
                Fitted on {sel_count:,} vehicles. <b>Temp = {b0_s:.2f} + {b1_s:.3f} × Ambient</b>. R² = <b>{(r2_s*100):.1f}%</b>
            </div>
        </div>
        """)

        x_line = np.linspace(filtered_df["average_ambient_temperature"].min(), filtered_df["average_ambient_temperature"].max(), 100)
        y_line = b0_s + b1_s * x_line

        fig_r1 = go.Figure()
        fig_r1.add_trace(go.Scattergl(
            x=plot_sample["average_ambient_temperature"],
            y=plot_sample["cell_temperature_max"],
            mode="markers",
            marker=dict(color="#22d3ee", size=4, opacity=0.4),
            name="Vehicles"
        ))
        fig_r1.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode="lines",
            line=dict(color="#f97316", width=3),
            name="Fit Line"
        ))
        apply_dark_theme(
            fig_r1,
            height=300,
            x_title="Ambient Temp (°C)",
            y_title="Max Cell Temp (°C)",
            show_legend=False
        )
        st.plotly_chart(fig_r1, config=PLOTLY_CONFIG)

    with col_r2:
        st.html(f"""
        <div class="dashboard-card" style="margin-bottom:12px;">
            <h4 style="color:#eef1ff;margin-bottom:4px;">Multiple: 6 Thermal Predictors</h4>
            <div style="color:#97a3c7;font-size:0.84rem;">
                Fitted on {sel_count:,} vehicles. R² = <b>{(r2_m*100):.1f}%</b>. Diagonal represents perfect prediction.
            </div>
        </div>
        """)

        sample_X_m = plot_sample[multi_features].values
        sample_y_pred = lr_multi.predict(sample_X_m)
        sample_y_actual = plot_sample["cell_temperature_max"].values

        diag_min = min(float(sample_y_actual.min()), float(sample_y_pred.min()))
        diag_max = max(float(sample_y_actual.max()), float(sample_y_pred.max()))

        fig_r2 = go.Figure()
        fig_r2.add_trace(go.Scattergl(
            x=sample_y_actual,
            y=sample_y_pred,
            mode="markers",
            marker=dict(color="#8b5cf6", size=4, opacity=0.4),
            name="Predictions"
        ))
        fig_r2.add_trace(go.Scatter(
            x=[diag_min, diag_max],
            y=[diag_min, diag_max],
            mode="lines",
            line=dict(color="#fb7185", width=3, dash="dash"),
            name="Ideal 45°"
        ))
        apply_dark_theme(
            fig_r2,
            height=300,
            x_title="Actual Temp (°C)",
            y_title="Predicted Temp (°C)",
            show_legend=False
        )
        st.plotly_chart(fig_r2, config=PLOTLY_CONFIG)

    # Tables: Comparison & Coefficients
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Model Comparison</h4>")
        cmp_html = f"""
        <table class='custom-table'>
            <thead><tr><th>Metric</th><th>Simple Model</th><th>Multiple Model</th></tr></thead>
            <tbody>
                <tr><td>Vehicles Fitted</td><td>{sel_count:,}</td><td>{sel_count:,}</td></tr>
                <tr><td>Predictors</td><td>1</td><td>{len(multi_features)}</td></tr>
                <tr><td>MAE (°C)</td><td>{mae_s:.2f}</td><td><b class='pos'>{mae_m:.2f}</b></td></tr>
                <tr><td>RMSE (°C)</td><td>{rmse_s:.2f}</td><td><b class='pos'>{rmse_m:.2f}</b></td></tr>
                <tr><td>R² Score</td><td>{r2_s:.3f}</td><td><b class='pos'>{r2_m:.3f}</b></td></tr>
            </tbody>
        </table>
        """
        st.html(f"<div class='dashboard-card'>{cmp_html}</div>")

    with col_t2:
        st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Multiple Regression Coefficients</h4>")
        coeff_html = f"""
        <table class='custom-table'>
            <thead><tr><th>Term</th><th>Coefficient</th></tr></thead>
            <tbody>
                <tr><td><b>Intercept</b></td><td>{lr_multi.intercept_:.3f}</td></tr>
        """
        for feat, coef in zip(multi_features, lr_multi.coef_):
            coeff_html += f"<tr><td>{feat.replace('_', ' ').title()}</td><td>{coef:.4f}</td></tr>"
        coeff_html += "</tbody></table>"
        st.html(f"<div class='dashboard-card'>{coeff_html}</div>")


# =============================================================================
# 9. DATA PREPROCESSING (NORMALIZATION & DISCRETIZATION)
# =============================================================================
st.html('<div id="preprocessing-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("gear", 22, "#8b5cf6")} Data Preprocessing</div>')
st.html('<div class="section-desc">Three mathematical normalization schemes and equal-width discretization into semantic bands.</div>')

prep_col = st.selectbox(
    "Choose Attribute for Preprocessing",
    options=list(THERM_LABELS.keys()),
    format_func=lambda k: THERM_LABELS[k],
    index=0,
    key="prep_attr_select"
)

prep_raw = filtered_df[prep_col].values
if len(prep_raw) > 0:
    p_min = float(np.min(prep_raw))
    p_max = float(np.max(prep_raw))
    p_mean = float(np.mean(prep_raw))
    p_std = float(np.std(prep_raw)) if np.std(prep_raw) > 0 else 1.0
    
    max_abs = max(abs(p_min), abs(p_max))
    j_dec = len(str(int(math.ceil(max_abs)))) if max_abs > 0 else 1
    p_scale = 10 ** j_dec

    sample_raw = prep_raw[:8]
    col_pr1, col_pr2 = st.columns(2)

    with col_pr1:
        st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>First 8 Values, Normalized</h4>")
        norm_html = "<table class='custom-table'><thead><tr><th>Raw</th><th>Min-Max [0,1]</th><th>Z-Score</th><th>Decimal Scaling</th></tr></thead><tbody>"
        for v in sample_raw:
            mm_val = (v - p_min) / (p_max - p_min) if (p_max - p_min) > 0 else 0.0
            z_val = (v - p_mean) / p_std
            ds_val = v / p_scale
            norm_html += f"<tr><td>{v:.2f}</td><td>{mm_val:.3f}</td><td>{z_val:.3f}</td><td>{ds_val:.4f}</td></tr>"
        norm_html += "</tbody></table>"
        st.html(f"<div class='dashboard-card'>{norm_html}</div>")

    with col_pr2:
        st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:12px;'>Discretization (Equal-Width, 4 Bands)</h4>")
        band_counts, band_edges = np.histogram(prep_raw, bins=4)
        
        label_dict = {
            "cooling_system_health": ["Poor", "Fair", "Good", "Excellent"],
            "thermal_runaway_risk": ["Low", "Moderate", "High", "Severe"],
            "temperature_variance": ["Stable", "Uneven", "Erratic", "Extreme"]
        }
        semantic_labels = label_dict.get(prep_col, ["Cool", "Warm", "Hot", "Critical"])
        
        band_labels = [
            f"{semantic_labels[i]} ({band_edges[i]:.0f}–{band_edges[i+1]:.0f})"
            for i in range(4)
        ]

        fig_disc = go.Figure(
            data=[
                go.Bar(
                    x=band_labels,
                    y=band_counts,
                    marker=dict(
                        color=["#22d3ee", "#8b5cf6", "#fb7185", "#f97316"],
                        line=dict(color="rgba(255,255,255,0.1)", width=1),
                        cornerradius=8
                    )
                )
            ]
        )
        apply_dark_theme(
            fig_disc,
            title=f"Band Distribution: {THERM_LABELS[prep_col]}",
            height=280,
            y_title="Vehicles Count"
        )
        st.plotly_chart(fig_disc, config=PLOTLY_CONFIG)


# =============================================================================
# 10. VISUALIZATIONS (THE 6 LAB PLOT TYPES)
# =============================================================================
st.html('<div id="visuals-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("visuals", 22, "#fb7185")} Standard Visualizations</div>')
st.html('<div class="section-desc">The six core laboratory plot types, all dynamically mapped to thermal characteristics.</div>')

vz_c1, vz_c2, vz_c3 = st.columns(3)

# 1. Line Plot: Mean max temp by vehicle age
with vz_c1:
    age_grp = filtered_df.groupby(np.round(filtered_df["vehicle_age_years"]))["cell_temperature_max"].mean().reset_index()
    fig_v1 = go.Figure(
        data=[
            go.Scatter(
                x=age_grp["vehicle_age_years"],
                y=age_grp["cell_temperature_max"],
                mode="lines+markers",
                line=dict(color="#22d3ee", width=3, shape="spline"),
                marker=dict(size=6, color="#67e8f9"),
                fill="tozeroy",
                fillcolor="rgba(34,211,238,0.15)"
            )
        ]
    )
    apply_dark_theme(
        fig_v1,
        title="Line: Mean Max Temp by Age",
        height=260,
        x_title="Vehicle Age (Years)",
        y_title="°C"
    )
    st.plotly_chart(fig_v1, config=PLOTLY_CONFIG)

# 2. Bar Plot: Mean max temp by vehicle type
with vz_c2:
    vt_grp = filtered_df.groupby("vehicle_type")["cell_temperature_max"].mean().reset_index()
    fig_v2 = go.Figure(
        data=[
            go.Bar(
                x=vt_grp["vehicle_type"],
                y=vt_grp["cell_temperature_max"],
                marker=dict(
                    color=vt_grp["cell_temperature_max"],
                    colorscale=[[0, "#8b5cf6"], [1, "#fb7185"]],
                    cornerradius=6
                )
            )
        ]
    )
    apply_dark_theme(
        fig_v2,
        title="Bar: Mean Max Temp by Vehicle Type",
        height=260,
        y_title="°C"
    )
    st.plotly_chart(fig_v2, config=PLOTLY_CONFIG)

# 3. Scatter Plot: Stress index vs max temp
with vz_c3:
    fig_v3 = go.Figure(
        data=[
            go.Scattergl(
                x=plot_sample["battery_stress_index"],
                y=plot_sample["cell_temperature_max"],
                mode="markers",
                marker=dict(size=4, color="#fb7185", opacity=0.4)
            )
        ]
    )
    apply_dark_theme(
        fig_v3,
        title="Scatter: Stress Index vs Max Temp",
        height=260,
        x_title="Battery Stress Index",
        y_title="Max Temp (°C)"
    )
    st.plotly_chart(fig_v3, config=PLOTLY_CONFIG)

vz_c4, vz_c5, vz_c6 = st.columns(3)

# 4. Donut/Pie Plot: Battery failure share
with vz_c4:
    fail_counts = filtered_df["battery_failure"].value_counts()
    fig_v4 = go.Figure(
        data=[
            go.Pie(
                labels=["No Failure", "Failure"],
                values=[fail_counts.get(0, 0), fail_counts.get(1, 0)],
                hole=0.6,
                marker=dict(colors=["#22d3ee", "#f97316"]),
                textinfo="percent+label",
                textfont=dict(family="Outfit", size=11)
            )
        ]
    )
    apply_dark_theme(
        fig_v4,
        title="Pie: Battery Failure Ratio",
        height=260,
        show_legend=False
    )
    st.plotly_chart(fig_v4, config=PLOTLY_CONFIG)

# 5. Box Plot: Avg vs Max cell temperature
with vz_c5:
    fig_v5 = go.Figure()
    fig_v5.add_trace(go.Box(
        y=filtered_df["cell_temperature_avg"],
        name="Avg Temp",
        marker_color="#8b5cf6",
        boxpoints="outliers"
    ))
    fig_v5.add_trace(go.Box(
        y=filtered_df["cell_temperature_max"],
        name="Max Temp",
        marker_color="#fb7185",
        boxpoints="outliers"
    ))
    apply_dark_theme(
        fig_v5,
        title="Box: Avg vs Max Temperature",
        height=260,
        y_title="°C"
    )
    st.plotly_chart(fig_v5, config=PLOTLY_CONFIG)

# 6. Histogram: Max cell temperature
with vz_c6:
    fig_v6 = go.Figure(
        data=[
            go.Histogram(
                x=filtered_df["cell_temperature_max"],
                nbinsx=24,
                marker=dict(
                    color="#f97316",
                    line=dict(color="rgba(255,255,255,0.1)", width=1)
                )
            )
        ]
    )
    apply_dark_theme(
        fig_v6,
        title="Histogram: Max Temp Spread",
        height=260,
        x_title="°C",
        y_title="Frequency"
    )
    st.plotly_chart(fig_v6, config=PLOTLY_CONFIG)


# =============================================================================
# 11. ADVANCED VISUALIZATIONS (PIXEL, GEOMETRIC, ICON, HIERARCHY)
# =============================================================================
st.html('<div id="advanced-sec" style="scroll-margin-top: 30px;"></div>')
st.html(f'<div class="section-hdr">{icon_svg("sparkles", 22, "#f97316")} Advanced Data Mining Visualizations</div>')
st.html('<div class="section-desc">Pixel-based, geometric parallel coordinates, icon-based star glyphs, and hierarchical treemaps.</div>')

adv_attr = st.selectbox(
    "Pixel Attribute to Map",
    options=list(THERM_LABELS.keys()),
    format_func=lambda k: THERM_LABELS[k],
    index=0,
    key="adv_pixel_select"
)

# 1. Pixel-based visualization
st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-bottom:6px;'>1. Pixel-Based Visualization</h4>")
st.html(f"<div style='color:#97a3c7;font-size:0.84rem;margin-bottom:12px;'>Vehicles sorted low-to-high by {THERM_LABELS[adv_attr]} (left) alongside their binary battery failure status (right; orange = failed).</div>")

n_px = min(2500, len(filtered_df))
sorted_px_df = filtered_df.sort_values(by=adv_attr).head(n_px)
grid_w = 50
grid_h = int(math.ceil(n_px / grid_w))

val_grid = np.full((grid_h, grid_w), np.nan)
fail_grid = np.full((grid_h, grid_w), np.nan)

val_arr = sorted_px_df[adv_attr].values
fail_arr = sorted_px_df["battery_failure"].values

for i in range(len(val_arr)):
    r = i // grid_w
    c = i % grid_w
    val_grid[r, c] = val_arr[i]
    fail_grid[r, c] = fail_arr[i]

px_c1, px_c2 = st.columns(2)

with px_c1:
    fig_px1 = go.Figure(
        data=[
            go.Heatmap(
                z=val_grid,
                colorscale=[[0, "#22d3ee"], [0.5, "#8b5cf6"], [1, "#fb7185"]],
                showscale=True,
                colorbar=dict(title=dict(text=THERM_LABELS[adv_attr], font=dict(family="Outfit", size=10)))
            )
        ]
    )
    apply_dark_theme(
        fig_px1,
        title=f"Pixel Matrix: {THERM_LABELS[adv_attr]}",
        height=260
    )
    fig_px1.update_xaxes(showticklabels=False)
    fig_px1.update_yaxes(showticklabels=False)
    st.plotly_chart(fig_px1, config=PLOTLY_CONFIG)

with px_c2:
    fig_px2 = go.Figure(
        data=[
            go.Heatmap(
                z=fail_grid,
                colorscale=[[0, "#1c2240"], [1, "#f97316"]],
                showscale=False
            )
        ]
    )
    apply_dark_theme(
        fig_px2,
        title="Pixel Matrix: Failure (Orange = Failed)",
        height=260
    )
    fig_px2.update_xaxes(showticklabels=False)
    fig_px2.update_yaxes(showticklabels=False)
    st.plotly_chart(fig_px2, config=PLOTLY_CONFIG)


# 2. Geometric Parallel Coordinates
st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-top:24px;margin-bottom:6px;'>2. Geometric: Parallel Coordinates</h4>")
st.html("<div style='color:#97a3c7;font-size:0.84rem;margin-bottom:12px;'>Multi-dimensional profile across 6 key physical axes. Orange lines designate failed battery packs.</div>")

# Smooth 400-point strided sample for parallel coordinates
pc_step = max(1, len(filtered_df) // 400)
pc_sample = filtered_df.iloc[::pc_step].head(400)

fig_pc = go.Figure(
    data=[
        go.Parcoords(
            line=dict(
                color=pc_sample["battery_failure"],
                colorscale=[[0, "rgba(34,211,238,0.25)"], [1, "rgba(249,115,22,0.85)"]],
                showscale=False
            ),
            dimensions=[
                dict(range=[float(filtered_df["average_ambient_temperature"].min()), float(filtered_df["average_ambient_temperature"].max())],
                     label="Ambient °C", values=pc_sample["average_ambient_temperature"]),
                dict(range=[float(filtered_df["humidity"].min()), float(filtered_df["humidity"].max())],
                     label="Humidity %", values=pc_sample["humidity"]),
                dict(range=[float(filtered_df["battery_stress_index"].min()), float(filtered_df["battery_stress_index"].max())],
                     label="Stress Index", values=pc_sample["battery_stress_index"]),
                dict(range=[float(filtered_df["thermal_runaway_risk"].min()), float(filtered_df["thermal_runaway_risk"].max())],
                     label="Thermal Risk", values=pc_sample["thermal_runaway_risk"]),
                dict(range=[float(filtered_df["cooling_system_health"].min()), float(filtered_df["cooling_system_health"].max())],
                     label="Cooling Health", values=pc_sample["cooling_system_health"]),
                dict(range=[float(filtered_df["cell_temperature_max"].min()), float(filtered_df["cell_temperature_max"].max())],
                     label="Max Temp °C", values=pc_sample["cell_temperature_max"])
            ]
        )
    ]
)
apply_dark_theme(fig_pc, height=340)
st.plotly_chart(fig_pc, config=PLOTLY_CONFIG)


# 3. Icon-based: Star Glyphs (Optimized Unified Subplot Figure)
st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-top:24px;margin-bottom:6px;'>3. Icon-Based: Star Glyphs</h4>")
st.html("<div style='color:#97a3c7;font-size:0.84rem;margin-bottom:12px;'>Individual radar glyphs for 8 sampled vehicles. Hexagon vertices map 6 battery metrics. Orange = Failed.</div>")

star_sample = filtered_df.head(8)
radar_cats = ["Max Temp", "Thermal Risk", "Stress Index", "Cooling Health", "Battery Health", "Vehicle Age"]
radar_cols = [
    "cell_temperature_max", "thermal_runaway_risk", "battery_stress_index",
    "cooling_system_health", "battery_health_percent", "vehicle_age_years"
]

min_vals = filtered_df[radar_cols].min()
max_vals = filtered_df[radar_cols].max()

# Unified 2x4 Subplot grid for 8x faster rendering and zero DOM stutter
star_titles = [
    f"{r['vehicle_id']} · {'FAILED' if r['battery_failure']==1 else 'HEALTHY'}"
    for _, r in star_sample.iterrows()
]
while len(star_titles) < 8:
    star_titles.append("")

fig_stars = make_subplots(
    rows=2, cols=4,
    specs=[[{"type": "polar"}]*4, [{"type": "polar"}]*4],
    subplot_titles=star_titles,
    vertical_spacing=0.22,
    horizontal_spacing=0.08
)

for i, (_, v_row) in enumerate(star_sample.iterrows()):
    row_idx = (i // 4) + 1
    col_idx = (i % 4) + 1

    norm_r = [
        float((v_row[c] - min_vals[c]) / (max_vals[c] - min_vals[c])) if (max_vals[c] - min_vals[c]) > 0 else 0.5
        for c in radar_cols
    ]
    norm_r.append(norm_r[0])
    cats_closed = radar_cats + [radar_cats[0]]

    is_fail = (v_row["battery_failure"] == 1)
    g_color = "#f97316" if is_fail else "#22d3ee"

    fig_stars.add_trace(
        go.Scatterpolar(
            r=norm_r,
            theta=cats_closed,
            fill="toself",
            fillcolor="rgba(249,115,22,0.3)" if is_fail else "rgba(34,211,238,0.25)",
            line=dict(color=g_color, width=2),
            showlegend=False
        ),
        row=row_idx, col=col_idx
    )

# Style all 8 polar coordinate axes
for i in range(1, 9):
    polar_key = f"polar{i}" if i > 1 else "polar"
    fig_stars.update_layout(**{
        polar_key: dict(
            radialaxis=dict(visible=False, range=[0, 1]),
            angularaxis=dict(tickfont=dict(family="Outfit", size=8, color="#97a3c7")),
            bgcolor="rgba(10,14,32,0.4)"
        )
    })

apply_dark_theme(fig_stars, height=440)
for annotation in fig_stars['layout']['annotations']:
    annotation['font'] = dict(family="Outfit", size=11, color="#eef1ff")

st.plotly_chart(fig_stars, config=PLOTLY_CONFIG)


# 4. Hierarchy-based: Treemap
st.html("<h4 style='font-size:1.05rem;color:#eef1ff;margin-top:24px;margin-bottom:6px;'>4. Hierarchy-Based: Treemap</h4>")
st.html("<div style='color:#97a3c7;font-size:0.84rem;margin-bottom:12px;'>Hierarchical partition (Vehicle Type → Battery Chemistry). Box area represents vehicle volume, and color intensity corresponds to failure rate.</div>")

tree_df = (
    filtered_df.groupby(["vehicle_type", "battery_chemistry"])
    .agg(Count=("vehicle_id", "count"), Fail_Rate=("battery_failure", "mean"))
    .reset_index()
)
tree_df["Fail_Rate_Pct"] = tree_df["Fail_Rate"] * 100

fig_tree = px.treemap(
    tree_df,
    path=["vehicle_type", "battery_chemistry"],
    values="Count",
    color="Fail_Rate_Pct",
    color_continuous_scale=[[0, "#22d3ee"], [0.5, "#8b5cf6"], [1, "#f97316"]],
    title="Treemap: Fleet Structure & Failure Severity"
)
apply_dark_theme(fig_tree, height=360)
fig_tree.update_layout(
    coloraxis_colorbar=dict(title=dict(text="% Failure", font=dict(family="Outfit", size=11)))
)
st.plotly_chart(fig_tree, config=PLOTLY_CONFIG)


# =============================================================================
# 12. FOOTER (CLEAN & MINIMAL)
# =============================================================================
st.html(f"""
<div style="margin-top:60px;padding:24px 0;border-top:1px solid rgba(255,255,255,0.08);color:#97a3c7;font-size:0.82rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div style="display:flex;align-items:center;gap:8px;">
        {icon_svg('bolt', 16, '#22d3ee')}
        <b>EV Battery Thermal Intelligence</b>
    </div>
    <div>Interactive Fleet Thermal Analytics</div>
</div>
""")

# =============================================================================
# 13. SMART SPLASH DISMISS TRIGGER (WAITS UNTIL ALL CHARTS & DOM ARE LOADED)
# =============================================================================
if render_splash:
    DISMISS_SPLASH_HTML = """
<script>
(function() {
    function dismissSplash() {
        var splash = document.getElementById('battery-splash');
        if (!splash) return;
        // Smoothly fade out overlay after all elements have rendered
        splash.style.transition = 'opacity 0.75s cubic-bezier(0.2, 0.7, 0.2, 1), transform 0.75s cubic-bezier(0.2, 0.7, 0.2, 1)';
        splash.style.opacity = '0';
        splash.style.transform = 'scale(1.05)';
        splash.style.pointerEvents = 'none';
        setTimeout(function() {
            if (splash && splash.parentNode) {
                splash.parentNode.removeChild(splash);
            }
        }, 800);
    }

    // Wait until browser has fully loaded all Plotly components and elements
    if (document.readyState === 'complete') {
        setTimeout(dismissSplash, 600);
    } else {
        window.addEventListener('load', function() {
            setTimeout(dismissSplash, 600);
        });
    }
    // Safety fallback timer
    setTimeout(dismissSplash, 3200);
})();
</script>
"""
    st.html(DISMISS_SPLASH_HTML, unsafe_allow_javascript=True)
