---
name: start-ticket
description: Start work on a Jira ticket by fetching details, creating a branch, and entering planning mode.
---

# Start Ticket

## Bundled helper scripts

Four bash helpers ship in this skill's `scripts/` directory. They wrap the Jira REST API so the rest of these instructions never need raw curl:

- `jira-ticket <KEY>` — fetch a ticket as markdown (title, status, description, comments)
- `jira-search <JQL> [--max N]` — search via JQL
- `jira-transition <KEY> ["<name>"]` — list available transitions, or execute one by name (case-insensitive)
- `jira-comment <KEY> -m "<markdown>"` (or read from stdin) — post a markdown comment, converted to ADF.
  Supports headings, bullet/ordered lists (2-space indent nests), tables (`| a | b |` over `|---|`),
  blockquotes, fenced code blocks, `---` rules, and inline `**strong**`, `*em*`, `` `code` ``,
  `~~strike~~`, `[text](url)`. A code span inside another mark — **`ref`** — posts as code
  without the decoration, since ADF forbids combining the code mark with any other.
  Run `jira-comment --help` for the authoritative list.

**Resolve the script directory once at the start of every invocation** and reuse it. The skill is installed under `~/.claude/plugins/`, but the exact subpath varies by version. Use:

```bash
JIRA_SCRIPTS=$(find ~/.claude/plugins -path '*/skills/start-ticket/scripts' -type d 2>/dev/null | head -1)
echo "$JIRA_SCRIPTS"   # confirm it resolved
```

Then invoke as `"$JIRA_SCRIPTS/jira-ticket" UP-1234` etc. Since bash variables don't persist across separate tool calls, either run helper invocations as a single bash command alongside the discovery, or hardcode the resolved absolute path for the rest of the session after the first `find`.

## Instructions

When this skill is invoked with a Jira ticket ID (e.g., `/start-ticket UP-1600`), help the user start work on that ticket.

### Steps

1. **Parse Arguments:**
   - Extract the Jira ticket ID from the command arguments
   - The ticket ID should match the pattern `{JIRA_PROJECT_KEY}-[0-9]+` (e.g., `UP-1600`)
   - If no ticket ID is provided, ask the user to provide one

2. **Validate Environment:**
   - Check that the following environment variables are set:
     - `JIRA_EMAIL` - User's Jira email for authentication
     - `JIRA_API_TOKEN` - API token for Jira authentication
     - `JIRA_BASE_URL` - Base URL of the Jira instance
   - If any are missing, inform the user which variables need to be configured
   - Resolve `$JIRA_SCRIPTS` (see "Bundled helper scripts" above) and verify the directory exists.

3. **Fetch Ticket Details:**
   - Run the bundled helper to fetch the ticket as markdown (title, status, description, comments — ADF auto-converted):
     ```bash
     "$JIRA_SCRIPTS/jira-ticket" {TICKET_ID}
     ```
   - If you need additional fields the helper doesn't print (Priority, Assignee, custom acceptance-criteria fields), fall back to the raw REST API:
     ```bash
     curl -s -X GET \
       -H "Accept: application/json" \
       -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
       "${JIRA_BASE_URL}/rest/api/3/issue/{TICKET_ID}"
     ```
   - If the helper or API call fails, display the error and stop

4. **Check for Existing Branches:**
   - Search for branches that already contain this ticket ID:
     ```bash
     git branch -a | grep -i {TICKET_ID}
     ```
   - If existing branch(es) are found:
     - Use the AskUserQuestion tool to ask the user whether to:
       - Switch to one of the existing branches (list them as options)
       - Create a new branch
     - If user chooses an existing branch, skip to step 6 (switch to that branch)

5. **Generate Branch Name** (only if creating a new branch):
   - Extract the ticket summary from the fetched ticket data
   - Convert the summary to a kebab-case slug:
     - Convert to lowercase
     - Replace spaces and special characters with hyphens
     - Remove consecutive hyphens
     - Truncate to a reasonable length (max ~50 characters for the description part)
   - Format: `{TICKET_ID}-{slug}` (e.g., `UP-1600-create-jira-skill`)

6. **Create or Switch Branch:**
   - If switching to an existing branch:
     ```bash
     git checkout {existing-branch}
     ```
   - If creating a new branch:
     ```bash
     git checkout -b {branch-name}
     ```

7. **Enter Planning Mode:**
   - Enter planning mode by running `/plan`

8. **Present Context:**
   - Display the ticket details in a clear format:
     - Ticket ID and Summary as heading
     - Status, Priority, Assignee
     - Full description
     - Acceptance criteria (if any)
   - Check with user
     - Ask if there is any specific guidance that should be considered while planning
   - Then begin creating an implementation plan based on:
     - The ticket requirements
     - The project's Documentation Driven Development workflow (see below and CLAUDE.md)
     - Relevant code patterns in the codebase

9. **Update Ticket Status (After Plan Accepted):**
   - Once the user has approved the plan and you're ready to begin implementation:
   - Check the ticket's current status from the fetched data (step 3)
   - If the status is "Open", transition it to "In Progress":
     ```bash
     "$JIRA_SCRIPTS/jira-transition" {TICKET_ID} "In Progress"
     ```
   - If the status is not "Open", skip this step (do not change the status)
   - Inform the user of the status update (or that it was skipped)

10. **Begin Implementation (Documentation Driven Development):**
    - The plan MUST follow the DDD workflow in this strict order. Each step is a prerequisite for the next.
    - By default, every ticket includes documentation and e2e tests. Before each step, ask the user if this specific ticket needs to skip it.

    **a. Documentation First:**
    - Ask the user: "Does this ticket need to skip documentation?" with options:
      - "No — write/update docs as usual" (Recommended)
      - "Yes — skip docs for this ticket"
    - If not skipped: update or create documentation in `docs/` describing the feature or change from a user's perspective
    - If skipped: proceed to the next step

    **b. Tests Second (write a failing test):**
    - Ask the user: "Does this ticket need to skip e2e testing?" with options:
      - "No — write a failing test first" (Recommended)
      - "Yes — skip e2e test for this ticket"
    - If not skipped:
      - Write an e2e test (Cypress/Cucumber `.feature` file) that validates the expected behavior
      - Run the test and confirm it FAILS — this proves the feature is not yet implemented
      - Use Puppeteer scripts to inspect the live local site (`http://localhost:8080`) when needed to understand page structure, DOM elements, CSS selectors, etc. Delete debug scripts before committing.
    - If skipped: proceed to the next step

    **c. Code Implementation (make the test pass):**
    - Implement the code changes
    - If an e2e test was written, run it and confirm it PASSES
    - Run any related existing tests to check for regressions
    - Run linting (`composer code-sniff-feature`) and static analysis (`composer static-analysis-feature`) and fix any issues

    **d. Commit all changes together:**
    - Documentation, tests, and implementation should be included in a single commit (or single PR)

11. **Create Pull Request and Follow Up:**
    - Create a PR targeting the `qa` branch. Include a **Test plan** section in the PR body with manual testing steps.
    - After the PR is created, ask the user: "Should I watch the GitHub workflow and update Jira when it completes?" with options:
      - "Yes — watch and update Jira" (Recommended)
      - "No — I'll handle it"
    - If yes:
      - Watch the GitHub Actions workflow run using `gh run watch --exit-status`
      - If the workflow **passes**:
        - **Transition the Jira ticket to "Ready for Feature Testing":**
          ```bash
          "$JIRA_SCRIPTS/jira-transition" {TICKET_ID} "Ready for Feature Testing"
          ```
        - **Post a comment to the Jira ticket** with the test plan and a link to the Pantheon environment:
          - Determine the Pantheon environment name from the branch (typically `pr-{PR_NUMBER}` or the multidev name from the CI logs)
          - The Pantheon environment URL follows the pattern: `https://pr-{PR_NUMBER}-myeap2.pantheonsite.io`
          - Compose the comment as markdown and post via the helper. Example:
            ```bash
            "$JIRA_SCRIPTS/jira-comment" {TICKET_ID} -m "$(cat <<'EOF'
            ## Test Plan

            - Step 1
            - Step 2
            - Step 3

            Pantheon environment: https://pr-{PR_NUMBER}-myeap2.pantheonsite.io

            GitHub PR: https://github.com/UCEAP/myeap2/pull/{PR_NUMBER}
            EOF
            )"
            ```
          - The comment should include:
            - A heading: "Test Plan"
            - The test plan steps (from the PR body)
            - A link to the Pantheon environment for testing
            - A link to the GitHub PR
        - **Remove the test plan from the PR body** using `gh pr edit` to keep the PR description concise, since the test plan now lives on the Jira ticket
      - If the workflow **fails**:
        - Report the failure to the user and show the failed job logs
        - Do NOT update the Jira ticket status
