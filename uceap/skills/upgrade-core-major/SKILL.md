---
name: upgrade-core-major
description: Upgrade Drupal to a new major version (e.g., 10.x to 11.x)
author: "Shaun Drong <sdrong@uceap.universityofcalifornia.edu> (Based on https://www.drupal.org/docs/upgrading-drupal)"
version: "1.0.0"
license: "MIT"
user_invocable: true
user_intent:
  - upgrade drupal major version
  - upgrade to drupal 11
  - major version upgrade
  - drupal 10 to 11
  - upgrade across major versions
whenToUse: When asked to upgrade Drupal across major versions (e.g., Drupal 10.x to 11.x). For patch/minor updates, use /uceap:upgrade-core instead.
---

# Drupal Major Version Upgrade Procedure

This skill guides upgrading Drupal across major versions (e.g., 10.x → 11.x) in UCEAP projects.

**WARNING**: Major version upgrades are complex and require significant planning and coordination. Do not proceed without team coordination.

## When to Use This Skill

- Upgrading from Drupal 10.x to 11.x (or any major version jump)
- Planning for a major version upgrade
- Assessing major version upgrade readiness

**For patch/minor updates** (e.g., 10.2.7 → 10.3.1), use `/uceap:upgrade-core` instead.

## Prerequisites

**Critical**: Major version upgrades require extensive preparation. Do not proceed until ALL prerequisites are met.

### 1. Team Coordination
- [ ] Major upgrade is planned and approved
- [ ] Team is aware of upgrade timeline
- [ ] Testing resources allocated
- [ ] Rollback plan documented

### 2. Environment Readiness
```bash
# Check current version
composer show drupal/core-recommended

# Verify PHP version meets new major version requirements
php -v

# Check Drush compatibility
vendor/bin/drush --version

# Ensure git is clean
git status
```

### 3. Contrib Module Compatibility Audit

**Before upgrading**, verify ALL contrib modules have versions compatible with the target major version:

```bash
# List all installed contrib modules
composer show "drupal/*" | grep -v "drupal/core"

# For each module, check drupal.org project page for compatibility
# Example: https://www.drupal.org/project/[module-name]
```

**Critical**: If any contrib module doesn't support the new major version:
- Find an alternative module
- Wait for compatibility update
- Remove the module if not essential

### 4. Custom Code Deprecation Scan

**Use Upgrade Status module** to identify deprecated API usage:

```bash
# Install Upgrade Status module
composer require drupal/upgrade_status
drush en upgrade_status -y

# Run comprehensive scan
drush upgrade_status:analyze

# Review report - address ALL errors before proceeding
```

The scan will show:
- Deprecated API usage in custom modules
- Deprecated API usage in themes
- Contrib modules with known compatibility issues

**You must fix ALL reported issues in custom code before upgrading.**

## Step-by-Step Procedure

**Note**: You will typically be provided with a specific target version number (e.g., 11.0.0). Use that version in the commands below.

### 1. Review Release Information

**Critical reading**:
- Release announcement: https://www.drupal.org/project/drupal/releases
- Change records: https://www.drupal.org/list-changes/drupal
- Breaking changes documentation
- API changes that affect your custom modules

**Document**:
- Breaking changes that affect your codebase
- Required custom code modifications
- Testing scenarios needed

### 2. Fix Deprecated Code

Based on the Upgrade Status scan:

```bash
# Work through each reported issue in custom modules
# Update deprecated API calls to new equivalents
# Test each fix in development

# Re-run scan after fixes
drush upgrade_status:analyze

# Repeat until scan is clean
```

**Do not proceed until the scan shows zero errors for custom code.**

### 3. Create Feature Branch

```bash
# Create upgrade branch
git checkout -b drupal-[VERSION]-upgrade

# Example: drupal-11.0-upgrade
```

### 4. Update Composer Dependencies

**UCEAP Standard Procedure (Exact Version Targeting):**

```bash
# Update main core packages (replace [VERSION] with target version, e.g., 11.0.0)
composer require drupal/core-recommended:[VERSION] \
  drupal/core-composer-scaffold:[VERSION] \
  drupal/core-project-message:[VERSION] \
  drupal/core-vendor-hardening:[VERSION] \
  --update-with-all-dependencies

# Update dev packages separately
composer require drupal/core-dev:[VERSION] --dev --update-with-all-dependencies
```

**Example for Drupal 11.0.0:**

```bash
composer require drupal/core-recommended:11.0.0 \
  drupal/core-composer-scaffold:11.0.0 \
  drupal/core-project-message:11.0.0 \
  drupal/core-vendor-hardening:11.0.0 \
  --update-with-all-dependencies

composer require drupal/core-dev:11.0.0 --dev --update-with-all-dependencies
```

**Important**: The `--update-with-all-dependencies` flag will also update contrib modules to compatible versions. Review the output carefully.

### 5. Resolve Dependency Conflicts

If composer reports conflicts:

```bash
# Get detailed conflict information
composer why-not drupal/core-recommended [target-version]

# Common resolutions:
# 1. Update incompatible contrib module to compatible version
# 2. Remove module if no compatible version exists
# 3. Update PHP version if required
```

### 6. Review What Changed

```bash
# Review all package updates
git diff composer.json
git diff composer.lock

# Check for unexpected changes
composer show drupal/core-recommended
composer show "drupal/*" | grep -v "drupal/core"

# Verify core version
drush status | grep "Drupal version"
```

**Critical**: Review the composer.lock diff carefully. Major upgrades often update dozens of packages.

### 7. Run Database Updates

**Note**: `drush updatedb` automatically activates maintenance mode during updates.

```bash
# Check for pending database updates
drush updatedb:status

# Run database updates
drush updatedb -y

# Clear all caches
drush cache:rebuild
```

**If database updates fail**: This is common in major upgrades. See troubleshooting section below.

### 8. Export Configuration

```bash
# Export all configuration
drush config:export -y

# Review what changed
drush config:export --diff

# Commit config changes with upgrade
git add config/
```

**Note**: Major version upgrades often modify configuration schema. Review config changes carefully.

### 9. Deactivate Maintenance Mode & Verify

```bash
# Deactivate maintenance mode
drush state:set system.maintenance_mode 0 --input-format=integer

# Clear cache
drush cache:rebuild

# Check for configuration drift
drush config:status
```

### 10. Comprehensive Testing

**Major version upgrades require extensive testing**:

**Essential Tests**:
- [ ] User login/logout (all user roles)
- [ ] Admin interface navigation
- [ ] Content creation/editing
- [ ] All custom module functionality
- [ ] All forms (especially complex forms like application)
- [ ] File uploads
- [ ] User permissions
- [ ] Cron jobs
- [ ] Custom themes render correctly

**Check logs aggressively**:
```bash
drush watchdog:show --severity=Error --count=50
drush watchdog:show --severity=Warning --count=50
```

**Run automated tests**:
```bash
composer unit-test
composer e2e-test-parallel
```

### 11. Check Contrib Module Compatibility

```bash
# Check for security vulnerabilities
composer audit

# Review if additional contrib updates available
composer outdated "drupal/*"

# Update contrib modules as needed
# Use /uceap:upgrade-drupal-module for individual modules
```

### 12. Validate Code Quality

```bash
# Run static analysis
composer static-analysis-feature

# Address any new deprecation warnings
# Major versions introduce NEW deprecations for the NEXT major version
```

### 13. Commit Changes

```bash
# Review all changes
git status
git diff

# Add all changed files
git add composer.json composer.lock config/

# Add any custom code fixes
git add web/modules/custom/ web/themes/

# Commit with comprehensive message
git commit -m "Upgrade Drupal core to [version]

Major version upgrade from [old] to [new]

Changes:
- Updated drupal/core-recommended: [old] -> [new]
- Fixed deprecated API usage in custom modules:
  - [module 1]: [brief description]
  - [module 2]: [brief description]
- Updated contrib modules for compatibility
- Ran database updates successfully
- Exported configuration changes
- Comprehensive testing completed

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Critical**: Document all custom code changes in the commit message.

### 14. Create Pull Request

```bash
# Push branch
git push -u origin drupal-[VERSION]-upgrade

# Create PR (use gh CLI)
gh pr create --base qa --title "Upgrade Drupal core to [VERSION]" --body "Major version upgrade. See commit message for details."
```

**PR Review Requirements**:
- Full team review required
- QA testing in staging required
- All automated tests must pass

## Common Issues & Solutions

### Issue: Database updates fail

Major version upgrades often have database update failures:

```bash
# Run updates one module at a time to isolate
drush updatedb --module=[module_name]

# If specific module fails:
# 1. Check module's upgrade path documentation
# 2. Check for known issues on drupal.org
# 3. May need to update module before core, or disable temporarily

# Common fix: Clear cache and retry
drush cache:rebuild
drush updatedb -y
```

### Issue: "Your currently installed version of [module] is not compatible"

```bash
# Option 1: Update the module to compatible version
composer require drupal/[module]:^[compatible-version]

# Option 2: Temporarily disable module
drush pm:uninstall [module]
# Then upgrade core
# Then reinstall compatible version

# Option 3: Remove module entirely if not essential
composer remove drupal/[module]
drush pm:uninstall [module]
```

### Issue: PHP version incompatibility

```bash
# Check core package requirements (including PHP version)
composer show drupal/core

# Review the 'requires' section for PHP version
# Drupal 11 example: PHP 8.3+ (check actual requirements in output)

# Update devcontainer PHP version if needed
# Update Pantheon PHP version in pantheon.yml
```

### Issue: Site breaks after upgrade

```bash
# Quick rollback
git reset --hard HEAD~1
composer install
drush cache:rebuild

# Or restore from container reset
uceap devcontainer-reset-db
composer install

# Investigate the issue before re-attempting
drush watchdog:show --severity=Error
```

### Issue: Custom module uses removed API

This is why Upgrade Status scan is critical:

```bash
# Re-run upgrade status
drush upgrade_status:analyze

# For each issue:
# 1. Read the change record link provided
# 2. Update code to new API
# 3. Test thoroughly
# 4. Re-scan until clean
```

### Issue: Theme rendering issues

Major versions may change theme layer:

```bash
# Check for deprecated theme hooks
# Review theme's .info.yml for compatibility
# May need to update theme's base theme or rebuild custom theme

# Clear theme cache
drush cache:rebuild
```

## Validation Checklist

Before considering the upgrade complete:

- [ ] Composer shows expected core version
- [ ] `drush updatedb:status` shows no pending updates
- [ ] `drush config:status` shows no configuration drift
- [ ] All critical user workflows tested successfully
- [ ] No PHP errors in logs
- [ ] Automated test suite passes (unit + e2e)
- [ ] Static analysis passes
- [ ] All custom modules function correctly
- [ ] All forms work (especially complex ones)
- [ ] Cron jobs execute successfully
- [ ] File uploads work
- [ ] User permissions correct
- [ ] Custom theme renders correctly
- [ ] Changes committed with detailed message
- [ ] Pull request created and reviewed

## Post-Upgrade Monitoring

After deploying to production (when that time comes):

- Monitor error logs aggressively for first 48 hours
- Watch for user-reported issues
- Check performance metrics haven't degraded
- Verify scheduled tasks (cron) running correctly
- Monitor database performance
- Check for contrib module security updates

## Planning Timeline

Major version upgrades take time:

**Recommended timeline:**
1. **Week 1**: Contrib module audit + Upgrade Status scan
2. **Week 2**: Fix deprecated code in custom modules
3. **Week 3**: Perform upgrade in development, initial testing
4. **Week 4**: Comprehensive testing, fix issues
5. **Week 5**: QA review in staging environment
6. **Week 6+**: Production deployment (coordinated)

**Do not rush major version upgrades.**

## References

- Drupal major version upgrade guide: https://www.drupal.org/docs/upgrading-drupal
- Change records: https://www.drupal.org/list-changes/drupal
- Upgrade Status module: https://www.drupal.org/project/upgrade_status
- API change documentation: https://api.drupal.org

## Integration with Other UCEAP Skills

- **After upgrade**: Use `/uceap:upgrade-drupal-module` to update contrib modules
- **Testing**: Use standard testing workflows from CLAUDE.md
- **Release**: After successful upgrade and testing, use `/uceap:release-notes`

## Notes for Skill Maintenance

**Update this skill when:**
- New Drupal major version is released
- Major version upgrade process changes
- Team develops new best practices for major upgrades
- Common failure patterns discovered

**Last reviewed**: 2026-08-20
