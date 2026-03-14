# 🔭 arXiv Digest

**Your personal arXiv paper curator** — fetches new papers, scores them with AI, and delivers a beautiful HTML digest to your inbox.

Created by [Silke S. Dainese](https://silkedainese.github.io) · [dainese@phys.au.dk](mailto:dainese@phys.au.dk) · [ORCID](https://orcid.org/0009-0001-7885-2439)

I built this for myself. I am a PhD student in astronomy at Aarhus University — not a software developer — and I wanted a smarter way to stay on top of new arXiv papers without spending an hour every morning. Other people in my department found it useful, so I cleaned it up and made it public. It is primarily aimed at people in physics and astronomy, but it will work for anyone on arXiv.

If you have suggestions, open an issue or [email me](mailto:dainese@phys.au.dk). I cannot promise to implement them — my research comes first.

> **For students:** The setup wizard has a guided track for **astronomy students** with pre-built keyword sets, AU faculty tracking, and telescope presets. If you are from another field and would like something similar for your speciality, [write me](mailto:dainese@phys.au.dk) and I will set it up.

*Built with the help of Claude Opus and Sonnet 4.6.*

---

## Quick Start

You need a GitHub account and an email address. That is it. AI scoring works out of the box — no API keys required.

### 1. Generate your config

**[Open the setup wizard →](https://arxiv-digest-setup.streamlit.app)**

Fill in your name, research description, keywords, and categories. The wizard generates a `config.yaml` file — download it.

> **Students:** Choose the "AU Astronomy Student" track for a pre-filled config with your department's faculty, telescopes, and keywords. You can customise it later.

### 2. Fork this repo

**[Fork arXiv Digest →](https://github.com/SilkeDainese/arxiv-digest/fork)**

This creates your own copy. Everything runs in your fork — nothing is shared back.

### 3. Upload your config

In your fork: **[Add file](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository) → Upload files** → drag in `config.yaml` → **Commit changes**.

### 4. Add email secrets

Your fork needs to know where to send emails. Go to **Settings → Secrets and variables → Actions** ([what are secrets?](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)) and add these three:

| Secret | What to put | Where to get it |
|--------|-------------|-----------------|
| `RECIPIENT_EMAIL` | Your email address | — |
| `SMTP_USER` | Your Gmail address | — |
| `SMTP_PASSWORD` | A Gmail App Password | **[Generate one here →](https://myaccount.google.com/apppasswords)** (requires [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification)) |

Using Outlook? See [Outlook setup](#outlook--office-365) below.

Sending to multiple people? Put a comma-separated list in `RECIPIENT_EMAIL`, e.g. `alice@uni.dk,bob@uni.dk`.

### 5. Send your first digest

**Actions → arXiv Digest → Run workflow → Run workflow**.

You should get an email within a few minutes. If something is wrong, the workflow log tells you exactly what to fix. This is the same button you can press anytime to trigger a manual run.

### 6. Done

Your digest now runs automatically **Mon/Wed/Fri at 9am Danish time** (07:00 UTC). No further action needed — papers show up in your inbox.

---

## Optional Upgrades

None of these are required. Everything works without them.

**Faster AI scoring** — your fork comes with a shared Gemini key. For faster, more reliable scoring, add your own:

| Secret | What you get | Where to get it |
|--------|--------------|-----------------|
| `GEMINI_API_KEY` | Your own Gemini key (free) | **[Google AI Studio →](https://aistudio.google.com/apikey)** |
| `ANTHROPIC_API_KEY` | Claude scoring (best quality) | **[Anthropic Console →](https://console.anthropic.com/)** — $5 lasts hundreds of digests |

Once you add your own key, set `own_api_key: true` in `config.yaml` to remove the nudge from your emails.

**Keyword tracking** — go to **Settings → Actions → General → Workflow permissions** → select **"Read and write permissions"**. The digest will track which keywords actually match papers over time.

**Feedback arrows** — set `github_repo: "yourusername/arxiv-digest"` in your `config.yaml`. Each paper card will show ↑/↓ arrows that nudge future scoring. ([How feedback works](#managing-your-digest))

---

## How It Works

The digest fetches new papers from arXiv, scores them against your interests, and emails you the best ones. AI scoring is included by default — no setup needed.

| Tier | Provider | Quality | What happens |
|------|----------|---------|--------------|
| 1 | **Claude** (Anthropic) | Best | Used if you add an `ANTHROPIC_API_KEY` |
| 2 | **Gemini 2.0 Flash** (Google) | Good | Used by default (shared key included) |
| 3 | **Keyword fallback** | Basic | Automatic fallback if AI is unavailable |

If one tier fails, it cascades to the next. You always get a digest. No money goes to the creator of this tool — API costs go directly to Anthropic/Google.

### Scoring details

1. **Keyword matching** — your keywords are checked against each paper's title and abstract, weighted by the importance you assigned (1–10). The matcher is fuzzy on purpose: plurals, hyphenation, and close variants like `planet` / `planetary` are treated as related.
2. **AI re-ranking** — the AI reads your `research_context` and re-ranks papers using that description. The more specific your research context, the better the scoring.
3. **Author boost** — papers by your `research_authors` get a relevance bump. Papers you authored yourself get a celebration section.

---

## Email Setup

### Gmail

1. Enable [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification)
2. Generate an [App Password](https://myaccount.google.com/apppasswords) — select "Mail" as the app
3. Use the App Password as your `SMTP_PASSWORD` secret

The default config uses Gmail — no changes needed in `config.yaml`.

### Outlook / Office 365

1. Set up an [App Password](https://account.microsoft.com/security) in your Microsoft account security settings
2. Use the App Password as your `SMTP_PASSWORD` secret
3. Update your `config.yaml`:

```yaml
smtp_server: "smtp.office365.com"
smtp_port: 587
```

---

## Config Reference

See [`config.example.yaml`](config.example.yaml) for all options with inline comments.

| Field | Description |
|-------|-------------|
| `research_context` | Free-text description of your research (used by AI scoring) — the more specific, the better |
| `keywords` | Dictionary of `keyword: weight` pairs (1–10) |
| `keyword_aliases` | Optional `keyword: [similar phrases]` overrides for brittle terminology |
| `categories` | arXiv categories to monitor |
| `self_match` | How your name appears in arXiv author lists — triggers a celebration section when you publish |
| `research_authors` | Authors whose papers get a relevance boost |
| `colleagues` | People/institutions whose papers always show; people can carry an optional `note` shown in the digest |
| `digest_mode` | `highlights` (fewer, higher-quality picks) or `in_depth` (wider net, more papers) |
| `recipient_view_mode` | `deep_read` (full cards) or `5_min_skim` (top 3 one-line summaries) |
| `github_repo` | Your fork's path, e.g. `janedoe/arxiv-digest` — enables self-service links and feedback arrows |

---

## Managing Your Digest

Every digest email includes self-service links at the bottom:

- **Edit interests** → opens `config.yaml` in GitHub's web editor
- **Pause** → links to the Actions tab (disable the workflow)
- **Re-run setup** → opens the setup wizard
- **Delete** → links to repo Settings (Danger Zone → Delete repository)

Each paper card also includes quick feedback arrows when `github_repo` is set:

- **↑** = relevant (more like this)
- **↓** = not relevant (less like this)

These create labeled GitHub issues (`digest-feedback`) that are automatically ingested to nudge future ranking.

### How to Unsubscribe

1. **Pause**: Go to your repo → Actions → arXiv Digest → click ⋯ → Disable workflow
2. **Delete**: Go to your repo → Settings → scroll to Danger Zone → Delete this repository
3. **Revoke email access**: Remove the App Password from your [Google](https://myaccount.google.com/apppasswords) or [Microsoft](https://account.microsoft.com/security) account

---

## Development

### Run locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"  # optional
export RECIPIENT_EMAIL="you@example.com"
export SMTP_USER="you@gmail.com"
export SMTP_PASSWORD="your-app-password"
python digest.py
```

To preview the digest in your browser without sending an email:

```bash
python digest.py --preview
```

### Run the setup wizard locally

```bash
cd setup
pip install -r requirements.txt
streamlit run app.py
```

---

## License

MIT — see [LICENSE](LICENSE).

**Created by [Silke S. Dainese](https://silkedainese.github.io)** · Aarhus University · Dept. of Physics & Astronomy
