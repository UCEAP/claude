---
name: upgrade-core
description: Upgrade Drupal core (patch/minor versions only)
author: "Shaun Drong <sdrong@uceap.universityofcalifornia.edu> (Based on https://www.drupal.org/docs/updating-drupal/updating-drupal-core-via-composer)"
version: "1.0.0"
license: "MIT"
user_invocable: true
user_intent:
  - upgrade drupal core
  - update drupal core
  - drupal security update
  - update drupal to
  - upgrade to drupal
whenToUse: When asked to upgrade Drupal core patch or minor versions (e.g., 10.2.7 to 10.3.1). For major version upgrades (e.g., 10.x to 11.x), use /uceap:upgrade-core-major instead.
---

# Drupal Core Update Procedure

This skill guides upgrading Drupal core in UCEAP projects using Composer-based workflows.

## When to Use This Skill

- Applying Drupal security updates
- Upgrading to latest patch/minor version
- Preparing for major version upgrades
- Resolving dependency conflicts involving core

## Prerequisites Check

Before starting, verify:

```bash
# Verify Composer version (requires Composer 2)
composer --version

# Check current Drupal version
composer show drupal/core-recommended

# Check for available core updates
composer outdated "drupal/core-*"

# Validate composer.json (warns about exact version constraints)
composer validate

# Check Drush version (need 12.4.3+ for Drupal 10.2+)
vendor/bin/drush --version

# Verify git status is clean
git status

# Ensure you're on the correct branch (typically qa or a feature branch)
git branch --show-current
```

## Step-by-Step Procedure

**Note**: You will typically be provided with a specific target version number (e.g., from a Jira ticket or security advisory). Use that version in the commands below.

### 1. Review Release Information

**For security updates:**
- Check https://www.drupal.org/security
- Read security advisory details
- Note any special upgrade considerations

**For feature updates:**
- Review release notes at https://www.drupal.org/project/drupal/releases
- Check for breaking changes and deprecations
- Review API changes that might affect custom modules

### 2. Update Composer Dependencies

**UCEAP Standard Procedure (Exact Version Targeting):**

When targeting a specific Drupal version, use the following commands:

```bash
# Update main core packages (replace [VERSION] with target version, e.g., 10.3.1)
composer require drupal/core-recommended:[VERSION] \
  drupal/core-composer-scaffold:[VERSION] \
  drupal/core-project-message:[VERSION] \
  drupal/core-vendor-hardening:[VERSION] \
  --update-with-all-dependencies

# Update dev packages separately
composer require drupal/core-dev:[VERSION] --dev --update-with-all-dependencies
```

**Examples:**

```bash
# Security update to specific patch version
composer require drupal/core-recommended:10.2.7 \
  drupal/core-composer-scaffold:10.2.7 \
  drupal/core-project-message:10.2.7 \
  drupal/core-vendor-hardening:10.2.7 \
  --update-with-all-dependencies

composer require drupal/core-dev:10.2.7 --dev --update-with-all-dependencies

# Minor version upgrade
composer require drupal/core-recommended:10.3.0 \
  drupal/core-composer-scaffold:10.3.0 \
  drupal/core-project-message:10.3.0 \
  drupal/core-vendor-hardening:10.3.0 \
  --update-with-all-dependencies

composer require drupal/core-dev:10.3.0 --dev --update-with-all-dependencies
```

**Preview Changes First (Recommended):**

Add `--dry-run` to simulate the update without executing:

```bash
composer require drupal/core-recommended:10.3.1 \
  drupal/core-composer-scaffold:10.3.1 \
  drupal/core-project-message:10.3.1 \
  drupal/core-vendor-hardening:10.3.1 \
  --update-with-all-dependencies \
  --dry-run
```

Review the output, then run without `--dry-run` to execute.

**Important Notes:**
- Some shells (zsh, fish) require quoting package names with special characters
- For other core update options, refer to: https://www.drupal.org/docs/updating-drupal/updating-drupal-core-via-composer
- Major version updates (e.g., 10.x → 11.x) require additional planning - see Major Version Upgrades section below

### 3. Review What Changed

```bash
# Check what packages were updated
git diff composer.lock

# Verify core version
drush status | grep "Drupal version"

# Check for pending database updates
drush updatedb:status
```

### 4. Run Database Updates

**Note**: `drush updatedb` automatically activates maintenance mode during updates.

```bash
# Run database updates (can also use drush updb)
drush updatedb -y

# Clear all caches
drush cache:rebuild
```

### 5. Export Configuration

After database updates, export configuration to capture any structural changes:

```bash
# Export all configuration
drush config:export -y

# Optional: Review what changed
drush config:export --diff
```

**Note**: Core updates may modify configuration structure. Commit any config changes with the update.

### 6. Deactivate Maintenance Mode & Verify

```bash
# Deactivate maintenance mode
drush state:set system.maintenance_mode 0 --input-format=integer

# Clear cache
drush cache:rebuild

# Check for configuration drift
drush config:status
```

### 7. Test Critical Functionality

Run through essential workflows to verify nothing broke:

**Universal UCEAP Tests:**
- User login/logout (test as anonymous user to verify maintenance mode is off)
- Admin interface access
- Check logs for new errors/warnings:
  ```bash
  drush watchdog:show --severity=Error --count=20
  drush watchdog:show --severity=Warning --count=20
  ```

**Project-Specific Tests:**
- Run automated test suite if available
- Manually test core features specific to the project
- Check custom module functionality (especially modules that extend core)

### 8. Check for Contributed Module Compatibility

```bash
# Check for security vulnerabilities
composer audit

# Review contrib module compatibility with new core version
composer outdated "drupal/*"
```

**Important**: Some contrib modules may need updates for compatibility with the new core version. Check project pages for compatibility information.

### 9. Validate Code Quality

```bash
# Run static analysis to catch deprecation usage
composer static-analysis-feature

# Address any new deprecation warnings in custom code
```

### 10. Commit Changes

```bash
# Review all changes
git status
git diff

# Add composer files (BOTH are required)
git add composer.json composer.lock

# Add any configuration changes
git add config/

# Commit with descriptive message
git commit -m "Update Drupal core to [version]

Security update addressing [SA-CORE-YYYY-NNN] / Feature update to [version]

- Updated drupal/core-recommended: [old] -> [new]
- Ran database updates successfully
- Exported configuration changes
- Tested [critical paths]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Critical**: Always commit `composer.json` AND `composer.lock` together. The lock file ensures identical package versions across environments.

**Note**: For major version upgrades (e.g., Drupal 10.x → 11.x), use `/uceap:upgrade-core-major` instead.

## Common Issues & Solutions

### Issue: Composer dependency conflicts

```bash
# Get detailed conflict information
composer why-not drupal/core-recommended [target-version]

# Common causes:
# 1. Contrib module doesn't support new core version yet
#    → Update or temporarily remove the module
# 2. PHP version too old
#    → Check core's PHP requirements and upgrade PHP if needed
# 3. Conflicting package constraints
#    → Update composer.json constraints as needed
```

### Issue: Database updates fail

```bash
# Run updates one module at a time to isolate the issue
drush updatedb --module=[module_name]

# Check error logs
tail -f /path/to/drupal/error.log

# Common fix: Clear cache first
drush cache:rebuild
drush updatedb -y
```

### Issue: Site breaks after update

```bash
# Quick rollback if needed
git reset --hard HEAD~1
composer install

# Clear all caches
drush cache:rebuild

# Restore config if it drifted
drush config:import -y
```

### Issue: "Composer detected issues in your platform"

This warning means your local PHP version differs from production. Usually safe to ignore in development, but verify:

```bash
# Check core package requirements (including PHP version)
composer show drupal/core
```

Review the `requires` section for PHP version requirements.

## Security Considerations

**Critical Security Updates:**
- Apply within 24-48 hours of release
- Test quickly but thoroughly
- Security updates are usually low-risk (targeted fixes)
- Don't skip security updates to wait for batching with other work

**Security Update Workflow:**
1. Create security update branch immediately
2. Apply update following this procedure
3. Fast-track testing
4. Deploy to production ASAP

## Validation Checklist

Before considering the update complete:

- [ ] Composer shows expected core version
- [ ] `drush updatedb:status` shows no pending updates
- [ ] `drush config:status` shows no configuration drift
- [ ] Critical user workflows tested successfully
- [ ] No PHP errors in logs
- [ ] Static analysis passes (or new issues addressed)
- [ ] Changes committed with clear message
- [ ] Security advisories addressed (if applicable)

## Post-Update Monitoring

After deploying to production:

- Monitor error logs for new issues
- Watch for user-reported problems
- Check performance metrics haven't degraded
- Verify scheduled tasks still running (cron)

## Environment-Specific Notes

**Development/Local:**
- Safe to experiment and rollback freely
- Use `git reset --hard` if update causes issues

**Staging:**
- Test deployment process
- Verify database updates run cleanly
- Validate config import/export workflow

**Production:**
- Always test in staging first
- Plan deployment window
- Have rollback plan ready
- Monitor closely after deployment

## References

- Drupal.org updates: https://www.drupal.org/project/drupal/releases
- Security advisories: https://www.drupal.org/security
- Composer Drupal docs: https://www.drupal.org/docs/develop/using-composer/manage-dependencies
- Upgrade path: https://www.drupal.org/docs/upgrading-drupal

## Integration with Other UCEAP Skills

This skill focuses on **core** updates. For other update tasks:

- **Contrib module updates**: Use `/uceap:upgrade-drupal-module`
- **Database operations**: Use `/uceap:load-db` to refresh from production
- **Release process**: Use `/uceap:release-notes` after updates are merged

## Notes for Skill Maintenance

**Update this skill when:**
- Drupal changes its update procedure
- New Composer best practices emerge
- UCEAP adds organization-wide update requirements
- Common failure patterns are discovered

**Last reviewed**: 2026-08-20
