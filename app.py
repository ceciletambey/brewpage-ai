"""
BrewPage — AI Marketing Strategy → Landing Page Engine for Coffee Shops
Big Data & AI in Marketing — Individual Assignment

Pipeline (two agents):
  1. STRATEGIST agent  -> makes the marketing decisions a strategist would:
        positioning, target customer, value proposition, tone, conversion goal.
  2. GENERATOR agent   -> turns that strategy into a real, styled landing page.
  3. (light) SCORER    -> self-scores the page on a marketing rubric so you have
        numbers to analyze in the report.

Run:  streamlit run app.py
Needs: GEMINI_API_KEY set in a .env file in the project root
"""

import os
import atexit
import json
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import queue
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

RUBRIC = [
    "positioning",     # is it clearly differentiated from generic cafes?
    "audience_fit",    # does copy speak to the stated target customer?
    "value_clarity",   # is the core value proposition obvious & specific?
    "cta_strength",    # is there one clear conversion goal?
    "tone_consistency" # does the voice stay consistent & on-brief?
]

# ----------------------------------------------------------------------------
# LLM HELPERS
# ----------------------------------------------------------------------------
def call_model(prompt, temperature=0.7):
    model = genai.GenerativeModel(MODEL_NAME)
    resp = model.generate_content(prompt, generation_config={"temperature": temperature})
    return resp.text


def parse_json(raw):
    clean = raw.strip().replace("```json", "").replace("```html", "").replace("```", "").strip()
    return json.loads(clean)


# ----------------------------------------------------------------------------
# AGENT 1 — STRATEGIST  (the marketing brain)
# ----------------------------------------------------------------------------
def make_strategy(shop):
    prompt = f"""You are a senior brand strategist for small hospitality businesses.
A coffee shop owner gives you raw notes. Turn them into a sharp marketing strategy.
Do NOT write website copy yet — make the strategic DECISIONS first.

COFFEE SHOP NOTES:
- Name: {shop['name']}
- Location / setting: {shop['location']}
- What makes it different: {shop['differentiator']}
- Vibe / atmosphere: {shop['vibe']}
- Target customer (owner's guess): {shop['target']}
- Main goal of the page: {shop['goal']}

Return ONLY a JSON object, no markdown:
{{
  "positioning": "one sentence: how this shop is positioned vs. generic cafes",
  "target_customer": "a crisp persona — who exactly we're talking to",
  "value_proposition": "the single most compelling reason to visit",
  "tone": "3-4 adjectives describing the voice",
  "conversion_goal": "the ONE action the page should drive",
  "key_messages": ["3 supporting points the page should make"]
}}"""
    return parse_json(call_model(prompt, temperature=0.6))


# ----------------------------------------------------------------------------
# AGENT 2 — GENERATOR  (strategy -> real landing page)
# ----------------------------------------------------------------------------
def cta_link_for(shop):
    """A CTA needs a real destination or the button is dead. Map each
    conversion goal to something that actually does something on click."""
    place = urllib.parse.quote(f"{shop['name']} {shop['location']}")
    return {
        "Get people to visit in person":
            f"https://www.google.com/maps/search/?api=1&query={place}",
        "Drive online orders / pre-orders":
            "mailto:hello@example.com?subject=Order%20Inquiry",
        "Sign up for a loyalty program":
            "mailto:hello@example.com?subject=Loyalty%20Program%20Sign-up",
        "Book the space for events":
            "mailto:hello@example.com?subject=Event%20Booking%20Inquiry",
    }.get(shop["goal"], "mailto:hello@example.com")


def make_page(shop, strategy):
    cta_link = cta_link_for(shop)
    prompt = f"""You are a senior designer at a boutique branding studio — the
kind hired by independent cafes who want to look like a real brand, not a
template. Build a complete, single-file HTML landing page for this coffee
shop, executing the marketing strategy below precisely.

SHOP: {shop['name']} — {shop['location']}
STRATEGY:
{json.dumps(strategy, indent=2)}

CTA_LINK (use this exact URL, do not invent your own): {cta_link}

STRUCTURE (in order):
1. Slim sticky nav: shop name (or a simple monogram/wordmark) on the left,
   one nav link or two, and a compact CTA button on the right.
2. Hero: headline + subhead executing the positioning, primary CTA button.
   Give it a real focal point (a large gradient/duotone panel standing in
   for a photo) — not just centered text on a flat color.
3. A 3-column "why us" grid built from the key messages, each with a small
   abstract icon (inline SVG or a styled CSS shape/emoji-free glyph) + a
   short headline + one line of copy. Avoid walls of text.
4. Atmosphere/about section: pairs a short paragraph with a visual block
   (placeholder gradient standing in for a photo) in an asymmetric two-
   column layout — alternate image-left/image-right if there's more than
   one such section.
5. A single-line "social proof" strip (e.g. a short quote in italics, or
   3 stat-style callouts like "Locally roasted" / "Open since ..." /
   neighborhood name) — keep this invented but plausible, never fake review
   counts or star ratings.
6. Footer: address/neighborhood, a final CTA button, minimal links.

DESIGN BAR (this is the part most AI-generated pages get wrong — fix it):
- Pick ONE deliberate color story from the vibe (e.g. a deep warm neutral +
  one accent), not a rainbow gradient. Background should mostly be a single
  calm tone; use the accent sparingly (CTA, small details).
- Pair a distinctive display serif or slab for headlines with a clean
  sans-serif for body text (load via Google Fonts <link>). No default
  system-font look.
- Use a consistent spacing scale (e.g. multiples of 8px) and generous
  whitespace — most amateur pages are too cramped.
- Buttons: one consistent style, rounded, with a visible hover state
  (transform/opacity transition) — not a flat unstyled <a>.
- Subtle details only: soft shadows, thin 1px borders, occasional rounded
  corners. No heavy drop-shadows, no neon, no more than one gradient on the
  whole page.
- Mobile-friendly: stack the grid/columns under ~700px.

RULES:
- ONE self-contained HTML file. All CSS in a <style> tag. No external JS
  frameworks. Google Fonts <link> is allowed.
- EVERY CTA button (nav, hero, footer) must be a real `<a href="{cta_link}">`
  styled as a button. Never use href="#" — it must actually navigate or
  open mail/maps when clicked.
- Use placeholder gradients/duotone panels instead of real images.
- Copy must execute the positioning, tone, and value proposition above —
  specific to this shop, never generic stock-cafe copy.

Return ONLY the raw HTML, starting with <!DOCTYPE html>. No markdown fences."""
    raw = call_model(prompt, temperature=0.8)
    return raw.strip().replace("```html", "").replace("```", "").strip()


# ----------------------------------------------------------------------------
# LIGHT SCORER  (numbers for the report)
# ----------------------------------------------------------------------------
def score_page(shop, strategy, page_html):
    prompt = f"""You are a strict marketing reviewer grading a junior copywriter's
work. You are hard to impress — a 5/5 is rare and means you found zero
faults. Most competent pages should land at 3-4. If you can name ANY
weakness for a dimension in your notes, that dimension cannot score above 4.

STRATEGY:
{json.dumps(strategy, indent=2)}

PAGE HTML (copy matters, ignore styling polish):
{page_html[:4000]}

Score 1-5 on each: positioning, audience_fit, value_clarity, cta_strength,
tone_consistency.

Return ONLY JSON:
{{"scores": {{"positioning":0,"audience_fit":0,"value_clarity":0,"cta_strength":0,"tone_consistency":0}},
  "notes": "one short paragraph: strongest and weakest aspects, naming the dimension each belongs to"}}"""
    return parse_json(call_model(prompt, temperature=0.3))


# ----------------------------------------------------------------------------
# MARKDOWN EXPORTS — one per agent, for the assignment report
# ----------------------------------------------------------------------------
def strategy_to_md(shop, strategy):
    lines = [f"# Strategist — {shop['name']}", ""]
    lines += [f"**Positioning:** {strategy['positioning']}", ""]
    lines += [f"**Target customer:** {strategy['target_customer']}", ""]
    lines += [f"**Value proposition:** {strategy['value_proposition']}", ""]
    lines += [f"**Tone:** {strategy['tone']}", ""]
    lines += [f"**Conversion goal:** {strategy['conversion_goal']}", ""]
    lines += ["**Key messages:**", ""]
    lines += [f"- {m}" for m in strategy["key_messages"]]
    return "\n".join(lines) + "\n"


def generator_to_md(shop, cta_link):
    return f"""# Generator — {shop['name']}

**Output:** one self-contained HTML landing page (see `landing_page.html`).

**CTA destination used on every button:** {cta_link}

**Sections produced:** sticky nav, hero, 3-column value grid, atmosphere/about
block, social-proof strip, footer with final CTA.

**Design brief given to the model:** one deliberate color story (not a
rainbow gradient), a display-serif/sans-serif font pairing, an 8px spacing
scale, subtle hover states on buttons, mobile-responsive grid.
"""


def score_to_md(shop, review):
    sc = review["scores"]
    avg = sum(sc.values()) / len(sc)
    rows = "\n".join(
        f"| {dim.replace('_', ' ').title()} | {val}/5 |" for dim, val in sc.items()
    )
    return f"""# Scorer — {shop['name']}

| Dimension | Score |
|---|---|
{rows}
| **Average** | **{avg:.2f}/5** |

**Reviewer notes:** {review['notes']}

_Note: the AI scores its own output — an LLM-as-judge limitation to flag in
the critical discussion._
"""


def score_label(avg):
    if avg >= 4.5:
        return "Excellent — near-flawless execution (rare)", "success"
    if avg >= 3.5:
        return "Strong — solid execution, minor gaps", "success"
    if avg >= 2.5:
        return "Decent — meets the basics, real gaps remain", "warning"
    return "Weak — strategy not well executed", "error"


# ----------------------------------------------------------------------------
# LIVE LINK — serve the generated page over a free Cloudflare quick tunnel
# so it's a real, clickable public URL, not just a download.
# ----------------------------------------------------------------------------
def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def stop_live_link():
    link = st.session_state.get("live_link")
    if not link:
        return
    for proc in (link["tunnel_proc"], link["server_proc"]):
        if proc.poll() is None:
            proc.terminate()
    shutil.rmtree(link["tmp_dir"], ignore_errors=True)
    st.session_state.pop("live_link", None)


def start_live_link(html):
    stop_live_link()
    tmp_dir = tempfile.mkdtemp(prefix="brewpage_")
    with open(os.path.join(tmp_dir, "index.html"), "w") as f:
        f.write(html)

    port = _free_port()
    server_proc = subprocess.Popen(
        ["python3", "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    tunnel_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )

    lines = queue.Queue()
    threading.Thread(
        target=lambda: [lines.put(l) for l in tunnel_proc.stdout] or lines.put(None),
        daemon=True,
    ).start()

    url, deadline = None, time.time() + 25
    while time.time() < deadline:
        try:
            line = lines.get(timeout=1)
        except queue.Empty:
            continue
        if line is None:
            break
        match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
        if match:
            url = match.group(0)
            break

    if not url:
        server_proc.terminate()
        tunnel_proc.terminate()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    # the hostname needs a few seconds to propagate through DNS before it's
    # actually reachable — wait for a real 200 instead of handing back a
    # link that 404s/NXDOMAINs the instant the user clicks it.
    reachable, verify_deadline = False, time.time() + 45
    while time.time() < verify_deadline:
        try:
            check = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "5", url],
                capture_output=True, text=True, timeout=7,
            )
            if check.stdout.strip() == "200":
                reachable = True
                break
        except Exception:
            pass
        time.sleep(1.5)

    if not reachable:
        server_proc.terminate()
        tunnel_proc.terminate()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return None

    st.session_state["live_link"] = {
        "url": url, "tmp_dir": tmp_dir,
        "server_proc": server_proc, "tunnel_proc": tunnel_proc,
    }
    return url


# ----------------------------------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------------------------------
st.set_page_config(page_title="BrewPage", page_icon=None, layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 3rem; max-width: 980px; }
h1 { font-weight: 600; letter-spacing: -0.02em; }
.bp-overline {
    text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.75rem;
    color: #8a8a8a; margin-bottom: 0.25rem;
}
.bp-rule { border: none; border-top: 1px solid #e6e6e4; margin: 1.75rem 0; }
[data-testid="stMetricValue"] { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

api_key = os.environ.get("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)

if "atexit_registered" not in st.session_state:
    atexit.register(stop_live_link)
    st.session_state["atexit_registered"] = True

st.markdown('<div class="bp-overline">Marketing strategy → landing page</div>',
            unsafe_allow_html=True)
st.title("BrewPage")
st.caption("Makes the marketing decisions a strategist would — positioning, "
           "audience, value proposition — then renders them into a landing "
           "page for an independent coffee shop.")

if not api_key:
    st.error("No GEMINI_API_KEY found. Add it to a .env file in the project "
             "root: GEMINI_API_KEY=your_key")

with st.expander("Pipeline & rubric"):
    st.markdown("**Pipeline:** Strategist → Generator → Scorer")
    st.markdown("**Rubric:** " + ", ".join(r.replace('_', ' ') for r in RUBRIC))

st.markdown('<hr class="bp-rule">', unsafe_allow_html=True)
st.subheader("Tell me about the coffee shop")
c1, c2 = st.columns(2)
with c1:
    name = st.text_input("Shop name", "Ember & Oak")
    location = st.text_input("Location / setting", "A quiet corner in Lavapiés, Madrid")
    vibe = st.text_input("Vibe / atmosphere", "Cozy, slow, lots of plants and warm wood")
with c2:
    differentiator = st.text_input("What makes it different",
        "Single-origin beans roasted in-house; the only pour-over bar in the neighborhood")
    target = st.text_input("Target customer (your guess)",
        "Remote workers and students who care about good coffee")
    goal = st.selectbox("Main goal of the page",
        ["Get people to visit in person", "Drive online orders / pre-orders",
         "Sign up for a loyalty program", "Book the space for events"])

shop = {"name": name, "location": location, "vibe": vibe,
        "differentiator": differentiator, "target": target, "goal": goal}

if st.button("Generate page", type="primary", disabled=not api_key):
    stop_live_link()
    with st.spinner("1/3 — Strategist is making the marketing decisions"):
        strategy = make_strategy(shop)
    with st.spinner("2/3 — Generator is building the landing page"):
        page_html = make_page(shop, strategy)
    with st.spinner("3/3 — Scoring the result"):
        review = score_page(shop, strategy, page_html)

    # stash for the report tab
    st.session_state["last"] = {"strategy": strategy, "html": page_html, "review": review}

if "last" in st.session_state:
    data = st.session_state["last"]
    tab_page, tab_strategy, tab_score = st.tabs(["Page", "Strategy", "Score"])

    with tab_page:
        components.html(data["html"], height=700, scrolling=True)

        live = st.session_state.get("live_link")
        b1, b2, b3, b4 = st.columns([1.3, 1.3, 1, 2])
        with b1:
            st.download_button("Download page (HTML)", data["html"],
                               file_name="landing_page.html", mime="text/html")
        with b2:
            st.download_button("Download generator output (.md)",
                               generator_to_md(shop, cta_link_for(shop)),
                               file_name="generator.md", mime="text/markdown")
        with b3:
            if st.button("Get public link"):
                with st.spinner("Opening a public tunnel and waiting for it "
                                 "to come online (up to ~45s)"):
                    url = start_live_link(data["html"])
                if not url:
                    st.error("Tunnel didn't come online in time. Try again.")
                else:
                    st.rerun()

        if live:
            st.success(f"Live now: {live['url']}")
            st.caption(
                "Anyone with this link can open the page right now. It's a "
                "free Cloudflare quick tunnel to a server on this machine — "
                "no account, but it stays up only while this app is running."
            )
            if st.button("Stop public link"):
                stop_live_link()
                st.rerun()

    with tab_strategy:
        s = data["strategy"]
        st.markdown(f"**Positioning** — {s['positioning']}")
        st.markdown(f"**Target customer** — {s['target_customer']}")
        st.markdown(f"**Value proposition** — {s['value_proposition']}")
        st.markdown(f"**Tone** — {s['tone']}")
        st.markdown(f"**Conversion goal** — {s['conversion_goal']}")
        st.markdown("**Key messages:**")
        for m in s["key_messages"]:
            st.markdown(f"- {m}")
        st.caption("This is the marketing-thinking step — the part that "
                   "separates this from a generic website builder.")
        st.download_button("Download strategist output (.md)",
                           strategy_to_md(shop, s),
                           file_name="strategist.md", mime="text/markdown")

    with tab_score:
        sc = data["review"]["scores"]
        avg = sum(sc.values()) / len(sc)
        label, kind = score_label(avg)
        getattr(st, kind)(f"{label} — average {avg:.2f}/5")
        st.caption("Scale: 1 weak · 2 below average · 3 decent · 4 strong · "
                   "5 exceptional (rare — means the reviewer found zero faults).")
        cols = st.columns(len(sc))
        for col, (dim, val) in zip(cols, sc.items()):
            col.metric(dim.replace("_", " "), f"{val}/5")
        st.markdown(f"**Reviewer notes:** {data['review']['notes']}")
        st.caption("Note: the AI scores its own output — an LLM-as-judge "
                   "limitation to flag in your critical discussion.")
        st.download_button("Download scorer output (.md)",
                           score_to_md(shop, data["review"]),
                           file_name="scorer.md", mime="text/markdown")
