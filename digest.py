"""
Science News for Silke 🔭
Fetches new arXiv papers, curates them with Claude, and sends a beautiful HTML digest.
"""

import os
import json
import smtplib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic

# ─────────────────────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────────────────────

CONFIG = {
    "categories": ["astro-ph.EP", "astro-ph.SR", "astro-ph.GA"],
    "keywords": [
        # ── Core: circumbinary & Gaia vbroad ──
        "circumbinary", "circumbinary planet", "Gaia", "vbroad", "vsini",
        "v sin i", "Gaia DR4", "Gaia DR3", "LAMOST", "macroturbulence",
        # ── Stellar rotation & Kraft break ──
        "Kraft break", "stellar rotation", "rotation velocity", "rotation period",
        "magnetic braking", "gyrochronology", "stellar spin-down",
        "angular momentum evolution", "Rossby number",
        "projected rotational velocity", "asteroseismic rotation",
        # ── Spin-orbit alignment & obliquities ──
        "spin-orbit alignment", "stellar obliquity", "obliquity",
        "Rossiter-McLaughlin", "Doppler tomography", "tidal realignment",
        # ── Binary stars & architecture ──
        "binary star", "spectroscopic binary", "eclipsing binary",
        "orbital architecture", "binary fraction",
        # ── Exoplanet demographics & interiors ──
        "exoplanet demographics", "radius valley", "mass-radius relation",
        "sub-Neptune", "water world", "planet interior",
        # ── Migration & tides ──
        "hot Jupiter migration", "high-eccentricity migration",
        "tidal dissipation", "Kozai-Lidov",
        # ── Methods (astrophysics-specific phrasing) ──
        "forward model", "hierarchical Bayesian", "simulation-based inference",
        "selection function",
    ],
    "known_authors": [
        "REDACTED", "Albrecht, S",
        "REDACTED", "REDACTED", "REDACTED", "REDACTED",
        "REDACTED", "Nielsen", "Luque",
    ],
    "days_back": 5,
    "max_papers": 8,
    "min_score": 4,
    "recipient_email": os.environ.get("RECIPIENT_EMAIL", ""),
}


Silke is a REDACTED,
REDACTED:
- REDACTED data
- REDACTED measurements
  (using NOT and LAMOST datasets)
- Stellar rotation velocities and the Kraft break (Teff 6000-8000 K)
- Forward-modelling Gaia broadening measurements (rotation + macroturbulence + instrumental floor ~5 km/s)
- Spin-orbit alignment and obliquity distributions (Rossiter-McLaughlin, Doppler tomography)
- Statistical methods: hierarchical Bayesian inference, Weibull distributions, forward models
"""

# ─────────────────────────────────────────────────────────────
#  ARXIV FETCHING
# ─────────────────────────────────────────────────────────────

def fetch_arxiv_papers(categories, days_back):
    papers = []
    for category in categories:
        params = {
            "search_query": f"cat:{category}",
            "start": 0,
            "max_results": 100,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
        print(f"  Fetching {category}...")
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                xml_data = response.read().decode("utf-8")
        except Exception as e:
            print(f"  Error: {e}")
            continue

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        for entry in root.findall("atom:entry", ns):
            published_str = entry.find("atom:published", ns).text
            published = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
            if published < cutoff:
                continue

            arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]

            known_flag = []
            for author in authors:
                for known in CONFIG["known_authors"]:
                    if known.lower() in author.lower():
                        known_flag.append(author)
                        break

            text_lower = (title + " " + abstract).lower()
            kw_hits = sum(1 for kw in CONFIG["keywords"] if kw.lower() in text_lower)

            papers.append({
                "id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published.strftime("%Y-%m-%d"),
                "category": category,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "known_authors": known_flag,
                "keyword_hits": kw_hits,
            })

    seen = set()
    unique = []
    for p in papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    print(f"  Found {len(unique)} papers total")
    return unique


def pre_filter(papers):
    filtered = [p for p in papers if p["keyword_hits"] > 0 or p["known_authors"]]
    filtered.sort(key=lambda p: (len(p["known_authors"]) * 5 + p["keyword_hits"]), reverse=True)
    return filtered[:30]


# ─────────────────────────────────────────────────────────────
#  CLAUDE ANALYSIS
# ─────────────────────────────────────────────────────────────

def analyse_papers(papers):
    if not papers:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("  ⚠️  ANTHROPIC_API_KEY not set — using keyword-only scoring")
        return _fallback_analyse(papers)

    client = anthropic.Anthropic(api_key=api_key)
    analysed = []

    for i, paper in enumerate(papers):
        print(f"  Analysing {i+1}/{len(papers)}: {paper['title'][:60]}...")

        prompt = f"""You are helping curate a personalised arXiv digest for an astronomer.

RESEARCHER CONTEXT:
{SILKE_CONTEXT}

PAPER:
Title: {paper['title']}
Authors: {', '.join(paper['authors'][:8])}
Category: {paper['category']}
Abstract: {paper['abstract']}

Respond with ONLY a valid JSON object (no markdown, no backticks):
{{
  "relevance_score": <integer 1-10>,
  "plain_summary": "<2-3 sentences explaining what they did, like explaining to a smart friend at a pub>",
  "why_interesting": "<1-2 sentences on why specifically relevant to Silke's work>",
  "emoji": "<one relevant emoji>",
  "highlight_phrase": "<punchy 5-8 word headline>",
  "kw_tags": ["<1-3 short keyword tags e.g. 'Gaia DR4', 'vsini', 'circumbinary'>"],
  "method_tags": ["<1-3 method tags e.g. 'forward model', 'TESS', 'eclipse timing'>"],
  "is_new_catalog": <true or false>,
  "cite_worthy": <true or false>,
  "new_result": "<2-4 word surprising result tag, or null>"
}}

Score: 10=circumbinary/Gaia vbroad, 8-9=stellar rotation/binaries, 6-7=related exoplanet science, 4-5=tangential, 1-3=not relevant
"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            analysis = json.loads(response.content[0].text.strip())
            paper.update(analysis)
            analysed.append(paper)
        except Exception as e:
            print(f"    Error: {e}")
            paper.update({
                "relevance_score": paper["keyword_hits"],
                "plain_summary": paper["abstract"][:300] + "...",
                "why_interesting": "Matched your keywords.",
                "emoji": "📄",
                "highlight_phrase": paper["title"][:50],
                "kw_tags": [], "method_tags": [],
                "is_new_catalog": False, "cite_worthy": False, "new_result": None,
            })
            analysed.append(paper)

    result = [p for p in analysed if p.get("relevance_score", 0) >= CONFIG["min_score"]]
    result.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
    return result[:CONFIG["max_papers"]]


def _fallback_analyse(papers):
    """Keyword-only scoring when API key is unavailable."""
    for p in papers:
        score = min(10, p["keyword_hits"] * 2 + len(p["known_authors"]) * 3)
        p.update({
            "relevance_score": max(score, 1),
            "plain_summary": p["abstract"][:300] + "...",
            "why_interesting": "Matched your keywords." + (
                f" Known author(s): {', '.join(p['known_authors'])}." if p["known_authors"] else ""
            ),
            "emoji": "📄",
            "highlight_phrase": p["title"][:50],
            "kw_tags": [], "method_tags": [],
            "is_new_catalog": False, "cite_worthy": False, "new_result": None,
        })
    result = [p for p in papers if p.get("relevance_score", 0) >= CONFIG["min_score"]]
    result.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
    return result[:CONFIG["max_papers"]]


# ─────────────────────────────────────────────────────────────
#  HTML RENDERING  (email-safe: inline styles + table layout)
# ─────────────────────────────────────────────────────────────

def render_html(papers, date_str):

    def score_bar(score):
        filled = round(score)
        return "".join(["●" if i < filled else "○" for i in range(10)])

    def accent_color(score):
        if score >= 9: return "#4ade80"
        if score >= 8: return "#63b3ed"
        if score >= 7: return "#ecc94b"
        if score >= 6: return "#f6ad55"
        if score >= 5: return "#b794f4"
        return "#718096"

    TAG = 'font-family:monospace;font-size:10px;letter-spacing:0.05em;text-transform:uppercase;padding:2px 8px;border-radius:3px;display:inline-block;margin:2px 3px 2px 0'

    def build_tags(p):
        score = p.get("relevance_score", 5)
        tags = []
        tags.append(f'<span style="{TAG};background:#1a2640;color:#63b3ed">{p["category"]}</span>')
        tags.append(f'<span style="{TAG};color:#4a5568">{p["published"]}</span>')
        for a in p.get("known_authors", []):
            tags.append(f'<span style="{TAG};background:#2a2210;color:#ecc94b">&#x1F44B; {a}</span>')
        if score >= 9:
            tags.append(f'<span style="{TAG};background:#2a1515;color:#fc8181">&#x1F525; must-read</span>')
        if score >= 8:
            tags.append(f'<span style="{TAG};background:#2a2210;color:#ecc94b">&#x1F4CC; thesis</span>')
        for kw in (p.get("kw_tags") or [])[:2]:
            tags.append(f'<span style="{TAG};background:#1a2640;color:#90cdf4">{kw}</span>')
        if p.get("is_new_catalog"):
            tags.append(f'<span style="{TAG};background:#1f1a30;color:#b794f4">&#x1F4E6; catalog</span>')
        if p.get("cite_worthy"):
            tags.append(f'<span style="{TAG};background:#152015;color:#68d391">&#x1F4CE; cite this</span>')
        if p.get("new_result"):
            tags.append(f'<span style="{TAG};background:#152015;color:#68d391">{p["new_result"]}</span>')
        return " ".join(tags)

    def build_method_tags(p):
        return " ".join(f'<span style="{TAG};background:#1f1a10;color:#c9895a">{t}</span>' for t in (p.get("method_tags") or []))

    # Paper cards — email-safe table layout with inline styles
    cards_html = ""
    for i, p in enumerate(papers):
        score = p.get("relevance_score", 5)
        ac = accent_color(score)
        authors_display = ", ".join(p["authors"][:5])
        if len(p["authors"]) > 5:
            authors_display += f" +{len(p['authors'])-5} more"
        top_label = f'<div style="font-family:monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;background:#4ade80;color:#0d1710;padding:3px 12px;display:inline-block;border-radius:3px;margin-bottom:12px">&#x2B51; Top pick</div>' if i == 0 else ''
        method_html = build_method_tags(p)
        footer_methods = f'<div style="margin-top:12px">{method_html}</div>' if method_html else ''

        cards_html += f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px">
      <tr><td style="background:#141824;border:1px solid #1e2535;border-left:4px solid {ac};border-radius:8px;padding:24px 26px 20px">
        {top_label}
        <!-- Header: tags + score -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="vertical-align:top;padding-bottom:10px">{build_tags(p)}</td>
            <td width="80" style="vertical-align:top;text-align:right;padding-bottom:10px">
              <span style="font-size:28px;line-height:1">{p.get('emoji','&#x1F52D;')}</span><br>
              <span style="font-family:Georgia,serif;font-size:26px;color:{ac};line-height:1">{score}</span><span style="font-size:13px;color:#4a5568">/10</span><br>
              <span style="font-family:monospace;font-size:8px;letter-spacing:2px;color:{ac};opacity:0.55">{score_bar(score)}</span>
            </td>
          </tr>
        </table>
        <!-- Title block -->
        <div style="font-family:Georgia,serif;font-size:14px;font-style:italic;color:#718096;margin-bottom:6px">{p.get('highlight_phrase','')}</div>
        <div style="font-family:sans-serif;font-size:16px;font-weight:bold;color:#e2e8f0;line-height:1.4;margin-bottom:5px"><a href="{p['url']}" style="color:#e2e8f0;text-decoration:none">{p['title']}</a></div>
        <div style="font-family:monospace;font-size:10px;color:#4a5568;margin-bottom:16px">{authors_display}</div>
        <!-- Summaries -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px">
          <tr><td style="background:#191e2d;border-radius:5px;padding:12px 14px">
            <div style="font-family:monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#4a5568;margin-bottom:6px">&#x1F9EA; What they did</div>
            <div style="font-family:sans-serif;font-size:13px;color:#94a3b8;line-height:1.75">{p.get('plain_summary','')}</div>
          </td></tr>
        </table>
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px">
          <tr><td style="background:#1c1a14;border:1px solid #2a2510;border-radius:5px;padding:12px 14px">
            <div style="font-family:monospace;font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:#4a5568;margin-bottom:6px">&#x2B50; Why it matters to you</div>
            <div style="font-family:sans-serif;font-size:13px;color:#b7a87a;line-height:1.75">{p.get('why_interesting','')}</div>
          </td></tr>
        </table>
        <!-- Footer -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="vertical-align:middle">{footer_methods}</td>
            <td width="120" style="text-align:right;vertical-align:middle">
              <a href="{p['url']}" style="font-family:monospace;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:{ac};text-decoration:none;border:1px solid {ac};padding:6px 14px;border-radius:3px;display:inline-block">Read paper &#x2192;</a>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>"""

    if not papers:
        cards_html = '<div style="text-align:center;padding:60px 24px;color:#4a5568;font-family:Georgia,serif;font-style:italic;font-size:18px">No highly relevant papers this period. The cosmos is quiet. &#x2615;</div>'

    avg_score = round(sum(p.get("relevance_score",0) for p in papers) / max(len(papers),1), 1)
    known_count = sum(1 for p in papers if p.get("known_authors"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Science News for Silke — {date_str}</title>
</head>
<body style="margin:0;padding:0;background:#0d0f14;color:#e2e8f0;font-family:Helvetica,Arial,sans-serif;font-weight:300;line-height:1.7;-webkit-font-smoothing:antialiased">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0d0f14">
<tr><td align="center">
<table width="680" cellpadding="0" cellspacing="0" border="0" style="max-width:680px;width:100%;background:#0d0f14">

  <!-- HEADER -->
  <tr><td style="padding:52px 44px 36px;background:#111520;border-bottom:1px solid #1a202c">
    <div style="font-family:monospace;font-size:10px;letter-spacing:0.3em;text-transform:uppercase;color:#63b3ed;margin-bottom:14px;opacity:0.75">arXiv &middot; astro-ph &middot; {date_str}</div>
    <div style="font-family:Georgia,serif;font-size:44px;font-weight:700;line-height:1.05;color:#f0f4ff;margin-bottom:6px">Science News<br>for <span style="font-style:italic;color:#ecc94b">Silke</span></div>
    <div style="font-size:13px;color:#4a5568;font-style:italic;margin-top:10px;font-family:Georgia,serif">Your bi-weekly window into the cosmos &#x2726; curated by Claude</div>
    <!-- Stats row -->
    <table cellpadding="0" cellspacing="0" border="0" style="margin-top:28px">
      <tr>
        <td style="padding-right:36px">
          <div style="font-family:Georgia,serif;font-size:32px;color:#ecc94b;line-height:1">{len(papers)}</div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:#4a5568;margin-top:3px">papers curated</div>
        </td>
        <td style="padding-right:36px">
          <div style="font-family:Georgia,serif;font-size:32px;color:#ecc94b;line-height:1">{known_count}</div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:#4a5568;margin-top:3px">familiar authors</div>
        </td>
        <td>
          <div style="font-family:Georgia,serif;font-size:32px;color:#ecc94b;line-height:1">{avg_score}</div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:#4a5568;margin-top:3px">avg relevance</div>
        </td>
      </tr>
    </table>
    <div style="margin-top:20px;font-family:monospace;font-size:10px;color:#2d3748;letter-spacing:0.08em;border-top:1px solid #1a202c;padding-top:16px">Monitoring astro-ph.EP &middot; astro-ph.SR &middot; astro-ph.GA &middot; last {CONFIG['days_back']} days &middot; threshold &#x2265; {CONFIG['min_score']}/10</div>
  </td></tr>

  <!-- SECTION DIVIDER -->
  <tr><td style="padding:20px 44px 14px;font-family:monospace;font-size:9px;letter-spacing:0.25em;text-transform:uppercase;color:#2d3748">&#x2500;&#x2500; All papers this edition &middot; {len(papers)} total &#x2500;&#x2500;</td></tr>

  <!-- PAPER CARDS -->
  <tr><td style="padding:0 24px 52px">
    {cards_html}
  </td></tr>

  <!-- FOOTER -->
  <tr><td style="padding:36px 44px;border-top:1px solid #141824;background:#0a0c11">
    <div style="text-align:center;font-size:18px;margin-bottom:18px;opacity:0.2;letter-spacing:10px">&#x2726; &middot; &#x2726; &middot; &#x2726;</div>
    <div style="font-family:monospace;font-size:9.5px;color:#2d3748;letter-spacing:0.1em;line-height:2.2;text-align:center">
      Science News for Silke &middot; Aarhus University &middot; Dept. of Physics &amp; Astronomy<br>
      Papers sourced from <a href="https://arxiv.org" style="color:#4a5568;text-decoration:none">arxiv.org</a> &middot; Summaries by Claude &middot; Running on GitHub Actions<br>
      <em>"Ad astra per aspera"</em>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
#  EMAIL SENDING — Gmail SMTP
# ─────────────────────────────────────────────────────────────

def send_email(html, paper_count, date_str):
    # Always save HTML artifact — useful for debugging and as a backup
    with open("digest_output.html", "w") as f:
        f.write(html)
    print("💾 Saved digest_output.html")

    recipient = CONFIG["recipient_email"]
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if not all([recipient, gmail_user, gmail_password]):
        print("⚠️  GMAIL_USER, GMAIL_APP_PASSWORD, or RECIPIENT_EMAIL not set — skipping email send.")
        return

    subject = f"🔭 Science News for Silke — {paper_count} papers · {date_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Science News for Silke <{gmail_user}>"
    msg["To"] = recipient
    msg.attach(MIMEText(f"Your arXiv digest for {date_str} — {paper_count} papers. Open in a browser for the full experience.", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, [recipient], msg.as_string())
        print(f"✅ Email sent to {recipient} via Gmail SMTP")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Gmail auth failed: {e}")
        print("   Make sure GMAIL_APP_PASSWORD is an App Password, not your regular password.")
        print("   Generate one at: Google Account > Security > 2-Step Verification > App passwords")
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        print("📋 Digest was saved as digest_output.html artifact — check Actions artifacts to download it.")


# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

def main():
    date_str = datetime.utcnow().strftime("%B %d, %Y")
    print(f"\n🔭 Science News for Silke — {date_str}")
    print("=" * 50)

    print("\n📡 Fetching papers from arXiv...")
    papers = fetch_arxiv_papers(CONFIG["categories"], CONFIG["days_back"])

    print("\n🔍 Pre-filtering...")
    candidates = pre_filter(papers)
    print(f"   {len(candidates)} candidates")

    print("\n🤖 Analysing with Claude...")
    final_papers = analyse_papers(candidates)
    print(f"   {len(final_papers)} papers made the cut")

    print("\n🎨 Rendering HTML...")
    html = render_html(final_papers, date_str)

    print("\n📧 Sending email...")
    send_email(html, len(final_papers), date_str)

    print("\n✨ Done!\n")


if __name__ == "__main__":
    main()

