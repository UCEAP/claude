# UCEAP software engineering team practices

These are the UCEAP IT software engineering team's standing practices. They are strong defaults, not absolute rules: every rule has exceptions. When a situation seems to call for an exception, raise it with the user and let them decide.

## Git history

- Commits that have been pushed to GitHub are shared, and the team does not rewrite them. No rebase, amend, squash, or force-push (including `--force-with-lease`) on a pushed branch, PR branches included. Someone else may have the branch checked out, and rewriting it breaks their copy.
- To bring a pushed branch up to date with its base, or to resolve conflicts, merge the base branch into it (for example `git merge origin/main`) and push normally.
- Rebasing, amending, and squashing local commits that have never been pushed is fine.
