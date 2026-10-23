---
name: jira
description: Read, search, comment on, and transition Jira tickets through the Jira REST API using bundled helper scripts. Use whenever a Jira key (e.g. UP-1234, UOS-149) appears in a commit, branch, PR, or conversation and you need its details, when the rationale for a change is plausibly recorded in a ticket, or when the user asks to search Jira, comment on a ticket, or change its status. Prefer these over the Atlassian connector or MCP tools.
---

# Jira

## Bundled helper scripts

Four bash helpers ship in this skill's `scripts/` directory. They wrap the Jira REST API so you never need raw curl:

- `jira-ticket <KEY>` — fetch a ticket as markdown (title, status, description, comments)
- `jira-search <JQL> [--max N]` — search via JQL. Prints `KEY [Status] Summary` lines.
- `jira-transition <KEY> ["<name>"]` — list available transitions, or execute one by name (case-insensitive)
- `jira-comment <KEY> -m "<markdown>"` (or read from stdin) — post a markdown comment, converted to ADF.
  Supports headings, bullet/ordered lists (2-space indent nests), tables (`| a | b |` over `|---|`),
  blockquotes, fenced code blocks, `---` rules, and inline `**strong**`, `*em*`, `` `code` ``,
  `~~strike~~`, `[text](url)`. A code span inside another mark — **`ref`** — posts as code
  without the decoration, since ADF forbids combining the code mark with any other.
  Run `jira-comment --help` for the authoritative list.

`jira-ticket` and `jira-search` are read-only; use them freely. `jira-comment` and `jira-transition` change the ticket for everyone watching it, so only run them when the user asks (or a skill they invoked says to).

**Resolve the script directory once at the start of every invocation** and reuse it. The skill is installed under `~/.claude/plugins/`, but the exact subpath varies by version. Use:

```bash
JIRA_SCRIPTS=$(find ~/.claude/plugins -path '*/skills/jira/scripts' -type d 2>/dev/null | head -1)
echo "$JIRA_SCRIPTS"   # confirm it resolved
```

Then invoke as `"$JIRA_SCRIPTS/jira-ticket" UP-1234` etc. Since bash variables don't persist across separate tool calls, either run helper invocations as a single bash command alongside the discovery, or hardcode the resolved absolute path for the rest of the session after the first `find`.

## Environment

The scripts read credentials from the devcontainer environment:

- `JIRA_EMAIL` — the developer's Atlassian account email
- `JIRA_API_TOKEN` — their Jira API token
- `JIRA_BASE_URL` — the Jira instance URL (`https://uceapit.atlassian.net`)

`JIRA_PROJECT_KEY` names the current project's key (e.g. `UP`), useful for scoping JQL. If a variable is missing, tell the user which one to set rather than working around it.

If you need fields the helpers don't print (priority, assignee, custom fields), fall back to the raw REST API v3:

```bash
curl -s -H "Accept: application/json" -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
  "${JIRA_BASE_URL}/rest/api/3/issue/{KEY}"
```
