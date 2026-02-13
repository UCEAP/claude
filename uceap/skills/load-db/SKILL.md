---
name: load-db
description: Download a database backup from Pantheon and import it into the local development environment. Can also be triggered by requests like "clone the live database", "load the dev db", or "pull the database from production".
user_invocable: true
user_intent:
  - load database
  - clone database
  - download database
  - pull database from pantheon
  - import database from pantheon
  - get a copy of the live database
---

# Load Database

## Instructions

When this skill is invoked — either via `/load-db` or through a natural language request like "clone the live database from december 12" — download a database backup from Pantheon and load it into the local development environment.

### Usage

```
/load-db                           # Interactive: choose environment and backup
/load-db live                      # Use latest backup from live environment
/load-db dev 2026-02-10            # Use backup from dev matching the given date
"clone the live database"          # Natural language: infer environment=live, pick latest
"load the db from test dec 12"     # Natural language: infer environment=test, date=dec 12
"pull down the production database"# Natural language: default to live, pick latest
```

### Interpreting Natural Language

When invoked through conversation rather than a slash command:
- Look for an environment name in the request (live, dev, test, qa, training, or any multidev name). If none mentioned, proceed to environment selection interactively.
- Look for a date reference in the request (e.g., "december 12", "feb 3", "yesterday", "last tuesday"). Convert it to a date string like `2026-02-10` for matching.
- If the user says "latest" or "most recent", skip backup selection and use the newest available.
- If the user says "production", treat it as the `live` environment.

### Steps

1. **Parse Arguments and Context:**
   - From slash command: first argument is environment, second is date
   - From natural language: extract environment and date from the user's message as described above
   - If both environment and date/latest are known, skip interactive selection steps

2. **Select Environment:**
   - If an environment was already determined, use it directly — skip interactive selection
   - Otherwise, list available environments using terminus:
     ```bash
     terminus env:list ${TERMINUS_SITE} --format=list --fields=id
     ```
   - Use the AskUserQuestion tool to let the user pick an environment from the list
   - Present the most commonly used environments first: `live`, `test`, `dev`, `qa`, then others
   - Include up to 3 options in the question, plus the user can type "Other" to specify a different environment
   - Recommend `live` as the default choice since it has production data

3. **Download Backup:**
   - **Latest backup (no date specified):** Skip the `backup:list` step entirely. Use `terminus backup:get` without `--file` to get the latest database backup URL directly, then download it in one command:
     ```bash
     curl -L "$(terminus backup:get ${TERMINUS_SITE}.{environment} --element=db)" --output /tmp/pantheon-db-backup.sql.gz
     ```
     This avoids fetching and parsing the full backup list JSON, which is large and wastes context tokens.
   - **Specific date requested:** Only in this case, list backups to find the matching one:
     ```bash
     terminus backup:list ${TERMINUS_SITE}.{environment} --element=db --format=json
     ```
     Filter to entries whose filename contains the target date string (e.g., `2026-02-10`), then download:
     ```bash
     curl -L "$(terminus backup:get ${TERMINUS_SITE}.{environment} --element=db --file={backup_filename})" --output /tmp/pantheon-db-backup.sql.gz
     ```
   - **Interactive (no environment or date):** List backups using the same `--element=db` filtered command above and use AskUserQuestion to let the user pick:
     - Present backups sorted by date (newest first)
     - Show the filename and size for each option
     - Recommend the most recent backup
     - Include up to 3 most recent backups as options, with "Other" available for older backups
   - If no database backups exist for the environment, inform the user and stop
   - If the download fails, inform the user and stop
   - Verify the downloaded file exists and has a non-zero size

4. **Import Database:**
   - **IMPORTANT:** The `db-rebuild.sh` script prepends `$(pwd)/` to positional file arguments (see line 80 of the script). You MUST either:
     - `cd /tmp` before invoking the script and pass the relative filename, OR
     - Pass the file using the `--` separator to avoid the path prepending
   - Run the import:
     ```bash
     cd /tmp && /usr/local/bin/db-rebuild.sh pantheon-db-backup.sql.gz
     ```
   - This script will:
     - Drop and recreate the local database
     - Detect compression format and decompress
     - Import the SQL into the local database
     - Run `drush deploy` to apply config and migrations
   - Stream the output to the user so they can see progress
   - This command takes a long time to run — use a generous timeout (at least 10 minutes)

5. **Clean Up:**
   - Remove the downloaded backup file:
     ```bash
     rm -f /tmp/pantheon-db-backup.sql.gz
     ```
   - Inform the user that the database has been loaded successfully
   - Report which environment and backup were used

### Error Handling

- If `TERMINUS_SITE` is not set, inform the user they need to set it (should be `myeap2` for this project)
- If terminus authentication fails, suggest running `terminus auth:login`
- If no backups are found for the selected environment, inform the user and suggest trying a different environment or creating a backup first with `terminus backup:create`
- If the download or import fails, preserve error output and present it to the user
