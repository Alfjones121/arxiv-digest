# SESSION_STATE Map

Scope: this table catalogs every explicit `st.session_state` read/write in `setup/app.py`. Streamlit widget keys that are only declared via `key=...` and never read or written through `st.session_state` are not included here.

Notes:
- `lazy` means the key is not initialized in the global defaults block; it is either read with `.get(..., fallback)` or only created after a later user action.
- All explicit `st.session_state` usage in this file is in the full Researcher setup flow. The Mini and hidden AU-student flows stop before the researcher wizard and only use widget-local state.
- `group_members` is exported in group mode even though it is not part of the base config schema summary in Phase 0b.

| session_state key | Type | Default | Config field | Set by step | Flows |
|---|---|---|---|---|---|
| `_invite_bundle` | `dict[str, str]` | `{}` | `internal` | `Session defaults; Welcome: Invite code` | `Researcher` |
| `_orcid_coauthor_counts` | `dict[str, int]` | `{}` | `internal` | `Session defaults; Step 1: About You (set/reset after ORCID import); Step 3: People to Follow suggestions` | `Researcher` |
| `_orcid_coauthor_map` | `dict[str, str]` | `lazy; treated as {}` | `internal` | `Step 1: About You (set/reset after ORCID import)` | `Researcher` |
| `_orcid_titles` | `list[str]` | `lazy; treated as []` | `internal` | `Step 1: About You (set/reset after ORCID import)` | `Researcher` |
| `_orcid_works_meta` | `list[dict[str, object]]` | `lazy; treated as []` | `internal` | `Step 1: About You (set/reset after ORCID import)` | `Researcher` |
| `_research_description_val` | `str` | `""` | `internal (backs research_context)` | `Session defaults; Step 1: About You` | `Researcher` |
| `_s2_digest_name` | `str` | `lazy; read as "arXiv Digest"` | `digest_name` | `Step 1: About You (advanced profile settings snapshot)` | `Researcher` |
| `_s2_tagline` | `str` | `lazy; read as ""` | `tagline` | `Step 1: About You (advanced profile settings snapshot)` | `Researcher` |
| `_s8_cron_expr` | `str` | `lazy; read as "0 7 * * 1,3,5"` | `internal` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_days_back` | `int` | `lazy; read as 4` | `days_back` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_digest_mode` | `str` | `lazy; read as "highlights"` | `digest_mode` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_max_papers` | `int` | `lazy; read as mode default (6 or 15)` | `max_papers (only if override enabled)` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_min_score` | `int` | `lazy; read as mode default (5 or 2)` | `min_score (only if override enabled)` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_override_max` | `bool` | `lazy; read as False` | `internal (gates max_papers export)` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_override_min` | `bool` | `lazy; read as False` | `internal (gates min_score export)` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_recipient_view_mode` | `str` | `lazy; read as "deep_read"` | `recipient_view_mode` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_schedule` | `str` | `lazy; read as "mon_wed_fri"` | `schedule` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_schedule_options` | `dict[str, str]` | `lazy; read as static frequency-label map` | `internal` | `Step 4: Delivery & Download` | `Researcher` |
| `_s8_send_hour_utc` | `int` | `lazy; read as 7` | `send_hour_utc` | `Step 4: Delivery & Download` | `Researcher` |
| `_s9_github_repo` | `str` | `lazy; read as ""` | `github_repo` | `Step 4: Delivery & Download` | `Researcher` |
| `_s9_smtp_port` | `int` | `lazy; read as 587` | `smtp_port` | `Step 4: Delivery & Download` | `Researcher` |
| `_s9_smtp_server` | `str` | `lazy; read as "smtp.gmail.com"` | `smtp_server` | `Step 4: Delivery & Download` | `Researcher` |
| `_show_coauthor_suggestions` | `bool` | `lazy; treated as False` | `internal` | `Step 3: People to Follow` | `Researcher` |
| `_show_manual_profile_fields` | `bool` | `lazy; treated as False` | `internal` | `Step 1: About You` | `Researcher` |
| `_show_schedule_picker` | `bool` | `lazy; treated as False` | `internal` | `Step 4: Delivery & Download` | `Researcher` |
| `ai_suggested_cats` | `list[str]` | `[]` | `internal (seeds category selection)` | `Session defaults; Step 2: What to Follow` | `Researcher` |
| `ai_suggested_kws` | `dict[str, int]` | `{}` | `internal (seeds keyword suggestions)` | `Session defaults; Step 2: What to Follow` | `Researcher` |
| `colleagues_institutions` | `list[str]` | `[]` | `colleagues.institutions` | `Session defaults; Step 3: People to Follow (advanced)` | `Researcher` |
| `colleagues_people` | `list[dict[str, str \| list[str]]]` | `[]` | `colleagues.people` | `Session defaults; Step 1 ORCID helpers; Step 3: People to Follow` | `Researcher` |
| `current_step` | `int` | `1` | `internal` | `Session defaults; wizard continue buttons in Steps 1-3` | `Researcher` |
| `group_orcid_members` | `list[dict[str, str \| int]]` | `[]` | `group_members (group-only extra output)` | `Session defaults; Step 1: About You (group import/clear)` | `Researcher` |
| `keywords` | `dict[str, int]` | `{}` | `keywords` | `Session defaults; Step 1 ORCID/Pure helpers; Step 2 AI scoring and keyword editor` | `Researcher` |
| `orcid_preview` | `dict[str, object] \| None` | `None` | `internal` | `Step 1: About You (staged pending import)` | `Researcher` |
| `paper_selector_widget` | `list[str]` | `lazy; created when ORCID titles exist` | `internal` | `Step 2: What to Follow paper selector` | `Researcher` |
| `profile_department` | `str` | `""` | `department` | `Session defaults; Step 1: About You (advanced profile settings)` | `Researcher` |
| `profile_institution` | `str` | `""` | `institution` | `Session defaults; Step 1 ORCID import; Step 1: About You` | `Researcher` |
| `profile_mode` | `str` | `"individual"` | `internal` | `Session defaults; profile-mode radio before Step 1` | `Researcher` |
| `profile_name` | `str` | `""` | `researcher_name` | `Session defaults; Step 1 ORCID import; Step 1: About You` | `Researcher` |
| `pure_confirmed_url` | `str` | `""` | `internal` | `Step 1: About You` | `Researcher` |
| `pure_scanned` | `bool` | `False` | `internal` | `Session defaults; Step 1 ORCID helpers` | `Researcher` |
| `research_authors` | `list[str]` | `[]` | `research_authors` | `Session defaults; Step 3: People to Follow (advanced)` | `Researcher` |
| `research_description` | `str` | `""` | `research_context` | `Session defaults; Step 1 ORCID helpers; Step 1: About You` | `Researcher` |
| `research_description_widget` | `str` | `lazy; widget starts from _research_description_val (initially "")` | `internal (widget mirror of research_context)` | `Step 1 ORCID helpers; Step 1: About You` | `Researcher` |
| `selected_categories` | `set[str]` | `lazy; initialized to set(ai_suggested_cats) or set()` | `categories` | `Step 2: What to Follow` | `Researcher` |
| `selected_papers` | `list[str]` | `[]` | `internal (influences AI suggestions only)` | `Session defaults; Step 1 ORCID helpers; Step 2 paper selector` | `Researcher` |
| `self_match` | `list[str]` | `[]` | `self_match` | `Session defaults; Step 1 ORCID import; Step 1: About You (advanced profile settings)` | `Researcher` |
| `user_anthropic_key` | `str` | `lazy; .get(..., "") / empty text input` | `internal` | `Welcome: AI setup (bring-your-own-key mode only)` | `Researcher` |
| `user_gemini_key` | `str` | `lazy; .get(..., "") / empty text input` | `internal` | `Welcome: AI setup (bring-your-own-key mode only)` | `Researcher` |

Config fields with no explicit `st.session_state` backing key in `setup/app.py`: `keyword_aliases`, `recipient_email`, `setup_url`.
