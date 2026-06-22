# BrewPage — AI Marketing Strategy → Landing Page Engine

Individual project for **Big Data & AI in Marketing**.
Topic: *Generative AI in content creation / AI-powered marketing workflows.*

## The marketing problem
Independent coffee shops need a web presence but can't afford a strategist or an
agency. Generic AI site builders generate templated pages with **no marketing
strategy** behind them — no positioning, no audience targeting, no conversion goal.
This project builds an AI that makes the *marketing decisions* first, then renders
them into a real landing page.

## How it works (two agents, one pipeline)
1. **Strategist agent** — turns the owner's raw notes into marketing decisions:
   positioning, target customer, value proposition, tone, conversion goal.
2. **Generator agent** — executes that strategy as a complete styled HTML page.
3. **Scorer** — self-scores the page on a 5-point marketing rubric (gives you
   numbers for the report).

This separation — *strategy before execution* — is the point. It's what makes it
a marketing project, not a website generator.

## Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```
Paste a free Gemini key (aistudio.google.com/apikey) in the sidebar. Fill in the
coffee shop details, hit **Generate page**, and you get three tabs: the live page,
the strategy behind it, and the score.

## What to put in the report
1. **Problem** — small cafes need strategy-driven web presence, not templates.
2. **Framework** — frame as a *strategy → execution* AI pipeline. Connect to
   course content on GenAI in content creation and marketing automation.
3. **System** — the Strategist/Generator split, the rubric, the scorer.
4. **Demo / results** — screenshot the strategy tab + the rendered page +
   the scores. Run it on 3-4 different cafes to show it generalizes.
5. **Critical discussion** — LLM-as-judge bias (it scores itself), where the
   strategy is generic vs. genuinely insightful, brand-safety, and why a human
   still validates before publishing.
6. **Conclusion** — what this says about GenAI lowering the cost of marketing
   strategy for small businesses.

## To make it more "yours"
- Run it on a few real local Madrid cafes and compare the strategies it produces.
- Tweak the Strategist prompt to enforce a positioning framework you like.
- Adjust the rubric in `RUBRIC` to match what you argue "good" means.
