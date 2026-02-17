---
name: release-notes
description: Create release notes for a UCEAP Portal release. Gathers PRs from GitHub milestone, fetches Jira ticket titles, creates a git tag, writes MkDocs documentation, creates a GitHub Release, and updates the version history index and navigation.
---

# Release Notes

## Instructions

When this skill is invoked with a version number (e.g., `/release-notes UP-V33.5` or `/release-notes 33.5`), create complete release documentation for that version.

### Usage

```
/release-notes UP-V33.5        # Full version tag format
/release-notes 33.5             # Short format (UP-V prefix added automatically)
```

### Steps

1. **Parse Arguments:**
   - Extract the version number from the command arguments
   - Accept either `UP-V33.5` or `33.5` format
   - Normalize to version number `33.5` for internal use and `UP-V33.5` for display
   - The filename format uses dashes: `up-v33-5.md` (NOT dots)
   - If no version is provided, ask the user to provide one

2. **Validate Environment:**
   - Check that the following environment variables are set:
     - `JIRA_EMAIL` - User's Jira email for authentication
     - `JIRA_API_TOKEN` - API token for Jira authentication
     - `JIRA_BASE_URL` - Base URL of the Jira instance
   - Verify GitHub CLI is authenticated: `gh auth status`
   - If any are missing, inform the user which variables need to be configured

3. **Find the GitHub Milestone:**
   - Look up the milestone by title `UP-V{version}`:
     ```bash
     gh api "/repos/UCEAP/myeap2/milestones?state=all&per_page=100" --jq '.[] | select(.title == "UP-V{version}")'
     ```
   - Extract the milestone number and the list of PRs:
     ```bash
     gh api "/repos/UCEAP/myeap2/issues?milestone={milestone_number}&state=closed&per_page=100" --jq '.[] | select(.pull_request != null) | {number, title}'
     ```
   - If the milestone is not found, inform the user and stop

4. **Find the Jira Release:**
   - Query Jira for the project versions:
     ```bash
     curl -s -X GET \
       -H "Accept: application/json" \
       -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
       "${JIRA_BASE_URL}/rest/api/3/project/UP/versions"
     ```
   - Find the version entry matching `UP-V{version}` and extract its `id`
   - Construct the Jira release URL: `https://uceapit.atlassian.net/projects/UP/versions/{id}/tab/release-report-all-issues`
   - If the Jira release is not found, the Jira Release link can be omitted from the release notes

5. **Find the Deployment Ticket:**
   - Search Jira for the deployment ticket using JQL:
     ```bash
     curl -s -X GET \
       -H "Accept: application/json" \
       -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
       "${JIRA_BASE_URL}/rest/api/3/search?jql=project%20%3D%20UP%20AND%20summary%20~%20%22PRODUCTION%20DEPLOYMENT%20V{version}%22&fields=summary"
     ```
   - The deployment ticket naming is inconsistent. The summary may match any of these patterns:
     - `PRODUCTION DEPLOYMENT V{version} {title}`
     - `V{version} PRODUCTION DEPLOYMENT {title}`
     - `PRODUCTION DEPLOYMENT V{version}: {title}`
   - Extract the release title — the descriptive text after the version pattern (e.g., "Academics and Finance Requests")
   - If no deployment ticket is found, use the AskUserQuestion tool to ask the user for a descriptive release title

6. **Fetch Jira Ticket Titles:**
   - For each PR in the milestone whose title contains a Jira ticket reference (`UP-XXXX`), extract the ticket ID
   - Fetch the Jira ticket summary for each unique ticket:
     ```bash
     curl -s -X GET \
       -H "Accept: application/json" \
       -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
       "${JIRA_BASE_URL}/rest/api/3/issue/UP-{number}?fields=summary"
     ```
   - Cache the results so each ticket is only fetched once (some PRs reference the same ticket)

7. **Categorize PRs:**
   - Split PRs into three groups:

   **Excluded** (do not include in release notes):
   - Version bump PRs: title contains `Bump version to`
   - Release merge PRs: title matches `UP-V{version}` exactly, or `UP-V{version} part` followed by a number

   **Features & Fixes** (PRs with Jira ticket references):
   - PR title contains `UP-XXXX`
   - Use the Jira ticket summary as the description (not the PR title)
   - Link format: `[UP-XXXX](https://uceapit.atlassian.net/browse/UP-XXXX) Jira summary ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))`
   - If multiple PRs reference the same Jira ticket, combine them into one entry with multiple PR links

   **Infrastructure & Maintenance** (everything else):
   - Use the PR title as the description
   - Link format: `PR title ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))`

   - If the milestone has very few non-excluded PRs (e.g., only meta PRs), inform the user and ask whether to examine the git diff between the previous tag and the new tag commit to find additional changes

8. **Identify the Tag Commit:**
   - First, check if the tag already exists:
     ```bash
     git tag -l "UP-V{version}"
     ```
   - If the tag already exists, skip tag creation (step 9) and use the existing tag
   - If the tag does not exist, find the most recent merge of qa into master that corresponds to this release:
     ```bash
     git log master --merges --first-parent --format="%H %s" | head -20
     ```
   - Present the candidate commit to the user for confirmation using AskUserQuestion
   - The commit message typically looks like: `Merge pull request #XXXX from UCEAP/qa`

9. **Create Annotated Git Tag:**
   - Skip this step if the tag already exists (detected in step 8)
   - Create the tag at the confirmed commit:
     ```bash
     git tag -a UP-V{version} {sha} -m "Release UP-V{version}"
     ```
   - Push the tag to the remote:
     ```bash
     git push origin UP-V{version}
     ```

10. **Create MkDocs Page:**
    - Write the release notes file at `docs/reference/version-history/up-v{version-with-dashes}.md`
    - Version dashes: replace dots with dashes (e.g., `33.5` becomes `33-5`, so filename is `up-v33-5.md`)
    - Use this exact format (H1 and H2 headings for MkDocs):

    ```markdown
    # UP-V{version}: {title}

    **Milestone:** [UP-V{version}](https://github.com/UCEAP/myeap2/milestone/{number}?closed=1)
    | **Jira Release:** [UP-V{version}](https://uceapit.atlassian.net/projects/UP/versions/{jira_version_id}/tab/release-report-all-issues)

    ## Features & Fixes

    - [UP-XXXX](https://uceapit.atlassian.net/browse/UP-XXXX) Jira ticket summary ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))
    - ...

    ## Infrastructure & Maintenance

    - PR title ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))
    - ...
    ```

    - If one section has no entries, omit that section entirely
    - If Jira Release was not found, omit the Jira Release line (keep only the Milestone line, without the `|` separator)

11. **Update Index and Navigation:**
    - **Index file** (`docs/reference/version-history/index.md`):
      - Add the new version as the first data row in the table (after the header row)
      - Determine the current month and year for the Date column
      - Format: `| [UP-V{version}](up-v{dashed}.md) | [{title}](up-v{dashed}.md) | [{Month Year}](up-v{dashed}.md) |`

    - **mkdocs.yml**:
      - Add the new version entry immediately after the `- Overview:` line under Version History
      - Format: `      - UP-V{version}: reference/version-history/up-v{dashed}.md`
      - Maintain descending order (newest first, right after Overview)

12. **Create GitHub Release:**
    - Check if a GitHub Release already exists for this tag:
      ```bash
      gh release view UP-V{version} 2>/dev/null
      ```
    - If it already exists, ask the user whether to overwrite it or skip
    - Create the release (note: GitHub Releases use ## and ### headings, not # and ##):
      ```bash
      gh release create UP-V{version} \
        --title "UP-V{version}: {title}" \
        --latest \
        --notes "$(cat <<'EOF'
      ## Features & Fixes

      - [UP-XXXX](https://uceapit.atlassian.net/browse/UP-XXXX) Jira ticket summary ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))

      ## Infrastructure & Maintenance

      - PR title ([#YYYY](https://github.com/UCEAP/myeap2/pull/YYYY))
      EOF
      )"
      ```
    - Note the heading level difference: GitHub Release notes use `##` and `###`, while MkDocs pages use `#` and `##`

13. **Build Docs:**
    - Run the documentation compiler to verify the new page works:
      ```bash
      composer compile-docs
      ```
    - If the build fails, diagnose and fix the issue before proceeding

14. **Report:**
    - Display a summary of everything that was created:
      - Git tag: `UP-V{version}` at `{sha}`
      - MkDocs page: `docs/reference/version-history/up-v{dashed}.md`
      - GitHub Release: link to the release
      - Index updated: `docs/reference/version-history/index.md`
      - Nav updated: `mkdocs.yml`
    - Remind the user to commit the documentation changes (MkDocs page, index, and mkdocs.yml)

### Error Handling

- If the GitHub milestone is not found, stop and inform the user
- If Jira API calls fail, display the error and continue with available data (use PR titles as fallback)
- If `gh auth status` fails, inform the user to authenticate with `gh auth login`
- If `composer compile-docs` fails, show the error output and ask the user how to proceed

### Notes

- Jira API v3 must be used (not v2) — all Jira endpoints use `/rest/api/3/`
- The deployment ticket naming is inconsistent across releases; the skill handles multiple patterns
- Version filenames always use dashes: `up-v33-5.md` (never `up-v33.5.md`)
- GitHub Release notes use `##` headings; MkDocs pages use `#` headings — do not mix these up
- If a milestone has very few substantive PRs, the release may have been deployed without a full milestone — check the git diff for the actual changes
- Multiple PRs may reference the same Jira ticket; combine them into a single entry with multiple PR links
