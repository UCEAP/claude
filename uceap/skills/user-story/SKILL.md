---
name: user-story
description: Generate a user story following best practices for the current feature branch
author: "Shaun Drong <sdrong@uceap.universityofcalifornia.edu> (Original: [Britt Crawford](https://github.com/britt/claude-code-skills/blob/main/skills/user-story-template/SKILL.md))"
version: "1.0.1"
license: "MIT"
user_invocable: true
user_intent:
  - create user story
  - write user story
  - generate user story
  - document user story
---

# User Story

## Overview

This skill creates well-formed user stories following product management best practices and the INVEST criteria. User stories are saved to the project's `user-stories/` directory using the current branch name as the filename.

User stories serve as the foundation for the Documentation Driven Development (DDD) workflow:
1. **User Story** - Document the feature from the user's perspective
2. **Documentation** - Write user-facing documentation
3. **Tests** - Write failing e2e tests based on acceptance criteria
4. **Implementation** - Make the tests pass

## Instructions

When this skill is invoked (e.g., `/user-story`), create a user story for the current feature branch.

### Steps

1. **Get Current Branch Name:**
   ```bash
   git rev-parse --abbrev-ref HEAD
   ```
   - This will be used as the filename for the user story
   - Example: `XX-1204-create-jira-skill` → `XX-1204-create-jira-skill.md`

2. **Check for Existing User Story:**
   - Determine the user story directory in the current workspace (default: `user-stories/`)
   - Check if a user story already exists for this branch
   - If it exists, ask the user whether to:
     - Update the existing user story
     - Create a new version
     - Cancel and exit

3. **Extract Context from Branch and Ticket:**
   - If the branch name contains a Jira ticket ID (pattern: `UP-\d+`):
     - Optionally fetch ticket details using the `start-ticket` helper scripts:
       ```bash
       JIRA_SCRIPTS=$(find ~/.claude/plugins -path '*/skills/start-ticket/scripts' -type d 2>/dev/null | head -1)
       "$JIRA_SCRIPTS/jira-ticket" {TICKET_ID}
       ```
     - Use ticket title, description, and acceptance criteria as context
   - Search for related documentation in `docs/` directory
   - Look for related code files to understand the feature scope

4. **Gather User Story Components (Interactive):**

   Use the AskUserQuestion tool to gather the three core components:

   **a. User Type/Persona:**
   - Ask: "Who is the primary user for this feature?"
   - Allow "Other" for custom user types

   **b. Action/Feature:**
   - Ask: "What action or feature does the user want?"
   - This should be concrete and specific
   - Example: "submit a study abroad application"
   - Avoid implementation details; focus on user intent

   **c. Benefit/Value:**
   - Ask: "What benefit or value does this provide to the user?"
   - This is the "why" - the business or user value
   - Example: "apply for programs that match my academic goals"

5. **Generate Acceptance Criteria:**

   Based on the context gathered and the user story components:
   - Propose 2-4 acceptance criteria scenarios
   - Each scenario should follow the Given-When-Then format
   - Make them specific and testable
   - Present them to the user for approval/modification

   Example:
   ```
   ### Scenario 1: Student submits complete application
   **Given** I am a logged-in student with all required documents uploaded\
   **When** I click the "Submit Application" button\
   **Then** my application status changes to "Submitted" and I receive a confirmation email
   ```

6. **Ask About Optional Sections:**

   Use AskUserQuestion to ask if the user wants to include:
   - Dependencies (other features, tickets, or systems this depends on)
   - Open Questions (unresolved questions that need answers)
   - Technical Notes (implementation considerations, architecture decisions)
   - Design Assets (links to mockups, wireframes, Figma files, etc.)

7. **Write the User Story File:**

   Create or update the file at `user-stories/{branch-name}.md` with this structure:

   ```markdown
   ---
   created: {YYYY-MM-DD}
   branch: {branch-name}
   ticket: {TICKET_ID} (if applicable)
   author: {git user name}
   ---

   # {Feature Title}

   ## User Story

   As a {user type}
   I want {action/feature}
   So that {benefit/value}

   ## Acceptance Criteria

   ### Scenario 1: {Name}
   **Given** {initial context}\
   **When** {action occurs}\
   **Then** {expected outcome}

   ### Scenario 2: {Name}
   **Given** {initial context}\
   **When** {action occurs}\
   **Then** {expected outcome}

   ## Dependencies
   {List dependencies or write "None"}

   ## Open Questions
   {List questions or write "None"}

   ## Technical Notes
   {List technical considerations or write "None"}

   ## Design Assets
   {List links to assets or write "None"}

   ---

   ## INVEST Criteria Checklist

   - [ ] **Independent**: Can this story be developed separately from other stories?
   - [ ] **Negotiable**: Are the details refinable during development?
   - [ ] **Valuable**: Does this provide clear user or business value?
   - [ ] **Estimable**: Can the team gauge the effort required?
   - [ ] **Small**: Can this be completed in one sprint?
   - [ ] **Testable**: Are there clear, verifiable success criteria?
   ```
   Note: In each scenarios section a '/' is need to display a line return when rendering the markdown. This only need for the middle section of text. The header and last line do not need it. This strictly a markdown rendering issue.

8. **Ensure Directory Exists:**
   ```bash
   mkdir -p user-stories
   ```

9. **Confirm and Save:**
   - Display a preview of the user story to the user
   - Ask for final confirmation
   - Write the file using the Write tool

10. **Git Operations (Optional):**
    - Ask the user: "Should I stage and commit this user story?"
    - If yes:
      ```bash
      git add user-stories/{branch-name}.md
      git commit -m "Add user story for {branch-name}"
      ```
    - If no: inform the user they can commit it later

11. **Next Steps Guidance:**
    - Remind the user of the DDD workflow order:
      1. ✅ User Story (just completed)
      2. ⏭️ Documentation (`docs/` directory)
      3. ⏭️ E2E Tests (Cypress `.cy.js` files)
      4. ⏭️ Implementation (code changes)
    - Suggest running `/plan` to begin implementation planning, which will reference this user story

## User Story Template Reference

### Core Format

```
As a [type of user]
I want [an action or feature]
So that [benefit or value]
```

### Acceptance Criteria Format

Use Given-When-Then for each scenario:
```
**Given** [initial context/state]\
**When** [action or event]\
**Then** [expected outcome]
```

## INVEST Criteria

User stories should meet these quality standards:

- **Independent**: The story can be developed and delivered separately from other stories
- **Negotiable**: Details can be refined during development; it's not a rigid contract
- **Valuable**: Provides clear value to users or the business
- **Estimable**: The development team can estimate the effort required
- **Small**: Can be completed within a single sprint (typically 1-2 weeks)
- **Testable**: Has clear criteria to verify when it's done

## Anti-Patterns to Avoid

- ❌ **Too technical**: "Refactor the authentication middleware to use JWT tokens"
  - ✅ **Better**: "As a user, I want to stay logged in across sessions so that I don't have to re-enter my credentials frequently"

- ❌ **Vague**: "As a user, I want the system to be faster"
  - ✅ **Better**: "As a student, I want application form saves to complete within 2 seconds so that I don't lose my work"

- ❌ **Missing rationale**: "As an admin, I want to export user data"
  - ✅ **Better**: "As an admin, I want to export user data to CSV so that I can analyze trends in student applications"

- ❌ **No acceptance criteria**: Story with no testable conditions
  - ✅ **Better**: Include specific Given-When-Then scenarios

## Integration with Other Skills

### With `/plan` (Planning Mode)

When the user runs `/plan`, Claude should:
1. Check if `user-stories/{branch-name}.md` exists
2. If it exists, Read the file and incorporate it into planning:
   - Use the user story to understand the feature's purpose
   - Reference acceptance criteria when designing the implementation
   - Include a "User Story" section in the plan that links to the file
3. If it doesn't exist, suggest creating one first with `/user-story`

### With `/start-ticket`

The `start-ticket` skill could optionally:
1. After creating a branch, suggest: "Would you like to create a user story? Run `/user-story`"
2. Or automatically invoke this skill if the user opts in

### With E2E Test Generation

When writing pure Cypress `.cy.js` test files:
1. Read the user story's acceptance criteria
2. Create a test file in `tests/cypress/e2e/` with descriptive naming: `{feature-name}.cy.js`
3. Convert Given-When-Then scenarios to Cypress test structure:
   ```javascript
   /**
    * E2E Test for: {Feature Title}
    * Based on user story: user-stories/{branch-name}.md
    */
   
   describe('Feature: {Feature Title}', () => {
     beforeEach(() => {
       // Login setup if needed
       cy.login('testuser', 'password'); // Use custom command or direct login
     });
   
     it('should {expected behavior from scenario}', () => {
       // Given - initial context
       cy.visit('/path-to-feature');
       
       // When - action occurs
       cy.get('[data-testid="action-button"]').click();
       
       // Then - expected outcome
       cy.contains('Expected success message');
       cy.get('[data-testid="result"]').should('be.visible');
     });
   });
   ```
4. Structure each scenario as a separate `it()` block
5. Use inline comments (`// Given`, `// When`, `// Then`) to maintain Given-When-Then clarity
6. Reference project-specific test conventions (login commands, test data setup) from CLAUDE.md

## Configuration

### Default Output Directory

`user-stories/`

This is relative to the project root. The directory will be created if it doesn't exist.

### Future Enhancement: Environment Variable

A future version could support a configurable directory via:
```bash
USER_STORY_DIR="${USER_STORY_DIR:-${WORKSPACE_FOLDER}/user-stories}"
```

For now, use the default location.

## Example User Story

Here's a complete example for reference:

```markdown
---
created: 2026-06-29
branch: XX-1600-add-application-signature-field
ticket: XX-1600
author: Jane Developer
---

# Add Digital Signature to Application Submission

## User Story

As a student
I want to digitally sign my study abroad application
So that I can legally acknowledge the terms and conditions without printing and scanning documents

## Acceptance Criteria

### Scenario 1: Student signs application before submission
**Given** I have completed all required application sections\
**When** I navigate to the Application Submission tab\
**Then** I see a signature canvas where I can draw my signature with my mouse or touchpad

### Scenario 2: Student cannot submit without signature
**Given** I have not provided a digital signature\
**When** I attempt to submit my application\
**Then** I see an error message "Signature required" and the submit button remains disabled

### Scenario 3: Signature is saved and displayed on submitted application
**Given** I have signed and submitted my application\
**When** a staff member views my submitted application\
**Then** they see my digital signature displayed in the Application Submission section

## Dependencies
- Canvas drawing library (investigate existing Drupal modules or JavaScript libraries)
- Signature data must be stored with the application entity

## Open Questions
- Should we support typed signatures as an accessibility alternative?
- What format should we store signatures in? (PNG, SVG, base64?)
- Do we need signature verification or timestamp for legal compliance?

## Technical Notes
- Use HTML5 Canvas element for drawing
- Store signature as base64-encoded PNG in a hidden textarea field
- Integrate with existing application form AJAX save mechanism
- Must work with existing `formIsValid()` client-side validation

## Design Assets
- None (use existing UCEAP form styling)

---

## INVEST Criteria Checklist

- [x] **Independent**: Can be developed without waiting for other features
- [x] **Negotiable**: Implementation details (canvas library, storage format) can be refined
- [x] **Valuable**: Eliminates manual paperwork, improves user experience
- [x] **Estimable**: Team estimates 3-5 days of development
- [x] **Small**: Can be completed in one sprint
- [x] **Testable**: Clear acceptance criteria with specific user interactions
```

## Tips for Writing Quality User Stories

1. **Start with the user's perspective**: Always frame the story from the user's point of view, not the system's or developer's

2. **Focus on value, not implementation**: Describe what the user wants to accomplish, not how the system should do it

3. **Keep it conversational**: User stories should read like natural language, not technical specifications

4. **Make acceptance criteria specific**: "The page loads quickly" is vague; "The page loads in under 2 seconds" is testable

5. **Include edge cases**: Don't just test the happy path; consider error states, validation failures, and boundary conditions

6. **Reference existing patterns**: Look at related features in the codebase to maintain consistency

7. **Collaborate**: User stories are meant to start conversations, not end them. Involve stakeholders in refinement.
