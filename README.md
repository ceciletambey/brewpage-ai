# BrewPage — AI Marketing Strategy → Landing Page Engine

Individual project for **Big Data & AI in Marketing**.
Topic: *Generative AI in content creation / AI-powered marketing workflows.*

A **three-agent LangGraph pipeline** for independent coffee shops: it makes the marketing
*decisions* a strategist would (positioning, audience, value proposition, tone, conversion
goal) before generating a single line of copy, then renders those decisions into a real,
styled landing page — optionally built around the shop's own uploaded photos — and lets you
iterate on the result with a feedback loop handled by a dedicated editor agent.

## The marketing problem
Independent coffee shops need a web presence but can't afford a strategist or an
agency. Generic AI site builders generate templated pages with **no marketing
strategy** behind them — no positioning, no audience targeting, no conversion goal.
This project builds an AI that makes the *marketing decisions* first, then renders
them into a real landing page.

## How it works (three agents, two LangGraph graphs)
1. **Strategist agent** — turns the owner's raw notes into marketing decisions:
   positioning, target customer, value proposition, tone, conversion goal.
2. **Generator agent** — executes that strategy as a complete, styled HTML page,
   using uploaded photos (if any) instead of placeholder gradients.
3. **Editor agent** — on demand, revises the existing page based on your feedback
   (and any new photos you attach), in a loop: give notes, get a revised page, repeat.

```
Generation pipeline:        START → strategist → generator → END
Editor loop (per revision): START → editor → END
```

This separation — *strategy before execution, execution before revision* — is the
point. It's what makes it a marketing project, not a website generator.

Photos never get sent to the LLM as raw pixel data: the generator/editor only ever see
`IMAGE_1`, `IMAGE_2`, ... placeholder tokens, and the real base64 photo gets swapped in only
at render time (`_inject_images` in `graph.py`). This keeps the editor loop cheap even after
several rounds of feedback with new photos attached.

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```
Get a free Gemini key (aistudio.google.com/apikey) and put it in a `.env` file in
the project root: `GEMINI_API_KEY=your_key`. (When deployed on Streamlit
Community Cloud, set it instead via the app's Secrets panel.) Fill in the coffee
shop details, optionally upload a few photos, hit **Generate page**, and you get
two tabs: the live page and the strategy behind it. The page is downloadable as a
self-contained HTML file. Below the page preview, a feedback box (plus an optional
photo uploader) lets you hand notes to the editor agent — e.g. "add a section
showcasing our brownies" with a brownie photo attached — and it revises the
existing page in place.

## What to put in the report
1. **Problem** — small cafes need strategy-driven web presence, not templates.
2. **Framework** — frame as a *strategy → execution → revision* AI pipeline. Connect
   to course content on GenAI in content creation and marketing automation.
3. **System** — the Strategist/Generator/Editor split, the LangGraph state, the
   token-based photo pipeline.
4. **Demo / results** — screenshot the strategy tab + the rendered page. Run it on
   3-4 different cafes (with and without photos) to show it generalizes, then show
   a before/after from one editor revision round.
5. **Critical discussion** — where the strategy is generic vs. genuinely insightful,
   brand-safety, and why a human still validates before publishing.
6. **Conclusion** — what this says about GenAI lowering the cost of marketing
   strategy for small businesses.

## To make it more "yours"
- Run it on a few real local Madrid cafes and compare the strategies it produces.
- Tweak the Strategist prompt in `graph.py` to enforce a positioning framework you like.
- Try it with and without uploaded photos on the same shop to compare results.
- Give the editor agent a few rounds of feedback and see how well it respects
  "change only what I asked" versus scope-creeping into the rest of the page.
