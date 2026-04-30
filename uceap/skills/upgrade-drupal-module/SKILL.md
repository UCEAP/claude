---
name: upgrade-drupal-module
description: Upgrade Drupal contributed modules. Auto-upgrades minor/patch releases. Prompts for major versions. Handles dependencies, patches, custom code updates, and security advisories.
---

# Upgrade Module Skill

Upgrades Drupal modules with intelligent version handling. Defaults to safe minor/patch upgrades. Prompts before major version upgrades that may have breaking changes.

## Usage

```
/upgrade-module <module-name> [module-name2] ...
```

**Behavior**:
- Minor/patch (6.2.0 → 6.3.0): Auto-upgrade, backwards-compatible
- Major (6.2.0 → 7.0.0): Prompt user, may have breaking changes

**Handles**:
- Version analysis with smart defaults
- Dependency resolution and ordering
- Security advisory detection
- Patch failure resolution
- Custom code updates (major versions only)
- Database updates and config export
- Comprehensive commit messages

## Prerequisites

- Dev/local environment (will warn if production)
- Clean git working tree
- Composer and Drush available

## Workflow

### Phase 1: Discovery & Analysis

1. Validate modules exist in composer.json
2. Check current versions from composer.lock
3. Find available versions: `composer show vendor/module --all`
4. Categorize each module:
   - Patch: 6.2.3 → 6.2.5 (bug fixes)
   - Minor: 6.2.3 → 6.4.0 (new features, BC)
   - Major: 6.2.3 → 7.0.0 (breaking changes)
5. Default target: latest minor (will prompt for major)

### Phase 2: Planning & User Confirmation

**For modules with major versions available**, prompt:
```
drupal/webform 6.2.3
- Latest minor: 6.5.0 (recommended, no breaking changes)
- Latest major: 7.0.2 (⚠️  may have breaking changes)

Upgrade to major version? [y/n/info]
```

If "info": Show CHANGELOG.md highlights, then re-prompt.

**Build upgrade plan** based on choices:
```
Upgrade Plan:
1. drupal/token: 1.11.0 → 1.13.0 [minor] ✓
2. drupal/webform: 6.2.3 → 7.0.0 [MAJOR] ⚠️

Dependencies: symfony/yaml 5.4.0 → 5.4.3
Custom code analysis will run for: webform

Proceed? [y/n]
```

### Phase 3: Execution (per module)

1. **Update composer.json** version constraint
   - Minor: `"^6.0"` (if not already)
   - Major: `"^6.0"` → `"^7.0"`

2. **Run composer update**
   ```bash
   composer update vendor/module --with-all-dependencies
   ```

3. **Handle security advisories** (if blocked):
   - Show vulnerabilities with CVE details
   - Present options:
     1. Cancel - fix security issues first
     2. Proceed anyway (may resolve some)
     3. Show more details
   - If proceeding:
     - `composer config audit.block-insecure false`
     - Run update
     - `composer config audit.block-insecure true`
     - Run `composer audit` to check if resolved
     - Warn if vulnerabilities remain

4. **Handle patch failures** (interactive):
   
   For each failed patch:
   - Analyze: Read patch, extract issue number, determine source
   - Check if still needed: Read CHANGELOG, check issue status
   - Present options:
     1. Remove (fixed in new version)
     2. Search drupal.org for updated patch
     3. Regenerate with increased fuzz
     4. Skip - handle manually
   - Execute choice and re-run composer update

5. **Verify**: Check composer.lock shows new version

### Phase 4: Custom Code Analysis & Updates

**Only runs for major version upgrades**

1. **Find breaking changes**:
   - Read vendor/MODULE/CHANGELOG.md (look for "Breaking", "Deprecated", "API changes")
   - Check drupal.org release notes
   - Extract specific changes (function signatures, removed APIs, etc.)

2. **Search custom code** for usage:
   ```bash
   grep -r "deprecated_function" web/modules/custom/ web/themes/custom/
   grep -r "use Drupal\\module_name\\" web/modules/custom/
   grep -r "hook_module_" web/modules/custom/
   ```

3. **Present findings**:
   ```
   Custom Code Impact (webform 6→7):
   
   Breaking changes:
   - getData() now requires $format parameter
   - hook_webform_submission_presave() signature changed
   
   Affected files:
   1. web/modules/custom/mymodule/WebformSubscriber.php:45
      Fix: Add 'raw' parameter to getData()
   2. web/modules/custom/mymodule/mymodule.module:89
      Fix: Add $update parameter to hook
   
   Implement fixes? [y/n]
   ```

4. **Implement fixes** (if confirmed):
   - Read each file for context
   - Update code using Edit tool
   - Verify syntax: `php -l file.php`
   - Check for cascading impacts

5. **Run static analysis** (if available):
   ```bash
   vendor/bin/phpstan analyse web/modules/custom
   ```

### Phase 5: Post-Upgrade Tasks

1. Database updates: `drush updatedb --yes`
2. Clear caches: `drush cache:rebuild`
3. Export config: `drush config:export --yes`
4. Status check: `drush status`
5. **Ask about testing**:
   ```
   Tests available: PHPUnit (156), Functional (42)
   Run tests? [y/n]
   ```

### Phase 6: Commit

**Generate commit message**:

For minor/patch only:
```
Upgrade contributed modules to latest compatible versions

Upgraded:
- drupal/token: 1.11.0 → 1.13.0 [minor]
- drupal/webform: 6.2.3 → 6.5.0 [minor]

Dependencies: symfony/yaml: 5.4.0 → 5.4.3

All upgrades backwards-compatible.
```

For major versions:
```
Upgrade contributed modules including major versions

Upgraded:
- drupal/webform: 6.2.0 → 7.0.0 [MAJOR]
- drupal/token: 1.11.0 → 1.13.0 [minor]

Dependencies: drupal/ctools: 3.14.0 → 4.0.0 (required by webform 7.x)

Patches:
- Removed webform-fix-12345.patch (fixed in 7.0.0)

Custom code updates for webform 7.0:
- Updated WebformSubscriber.php getData() signature
- Fixed hook_webform_submission_presave() parameters

Security advisories: 2 detected, 0 remain after upgrade
```

**Commit**:
```bash
git add composer.json composer.lock patches/ web/modules/custom/ web/themes/custom/
git commit -m "$(cat <<'EOF'
[message here]
EOF
)"
```

## Finding Breaking Changes

**Priority order**:
1. `vendor/drupal/MODULE/CHANGELOG.md` - Look for "Breaking", "Deprecated", "API"
2. `vendor/drupal/MODULE/UPGRADE.md` or `UPGRADE.txt`
3. Drupal.org release notes: `https://www.drupal.org/project/MODULE/releases/VERSION`
4. Change records: `https://www.drupal.org/list-changes/MODULE`
5. Git log: `cd vendor/drupal/MODULE && git log 6.0.0..7.0.0 --grep="break\|deprecat"`

**Quick search**:
```bash
grep -i "deprecat\|break\|remov" vendor/drupal/MODULE/CHANGELOG.md
grep -r "@deprecated" vendor/drupal/MODULE/src/
```

## Patch Management

**Drupal.org patches**: URL contains `drupal.org/files/issues`, has issue ID
**Custom patches**: In `patches/` directory, no drupal.org URL

**When patch fails**:
- **Remove if**: Issue marked "Fixed" in target version, or code inspection shows fix included
- **Update if**: Issue still active, newer patch available in issue queue
- **Skip if**: Uncertain, needs manual review

**Check issue status**: Extract issue ID from patch URL → visit `drupal.org/project/MODULE/issues/ID`

## Error Handling

**Security advisories blocked**:
- Never auto-bypass - always present to user
- Temporarily disable if user chooses to proceed
- Always re-enable after update
- Document in commit if encountered

**Dependency conflicts**:
- Update conflicting dependency first
- Adjust upgrade order

**Database update fails**:
- Do not commit
- Report for manual intervention

**PHP version incompatible**:
- Report required PHP version
- Suggest environment update

## Tips

1. Default upgrades are safe (minor/patch only)
2. Use "info" option to review major version changes
3. Grep custom code before accepting major upgrades to estimate impact
4. Test major upgrades thoroughly, especially with custom integrations

## Troubleshooting

**"No version satisfying XYZ"**: Check `composer show vendor/module --all`

**"Requirements could not be resolved"**: Dependency conflict - try updating dependencies first, may need core upgrade

## Notes

- Review composer output for deprecation warnings
- Major upgrades may require custom code changes
- Check module upgrade guide on drupal.org
- Use `composer why vendor/module` to understand dependencies