# EP-XXXX: [Title] - Implementation Plan

**Status:** Draft | Review | Approved | In Progress | Completed  
**Created:** YYYY-MM-DD  
**Updated:** YYYY-MM-DD  
**Phase:** Implementation Planning & Execution
**Requirements Document:** `docs/enhancements/pending/EP-XXXX-requirements.md`
**Design Document:** `docs/enhancements/pending/EP-XXXX-design.md`

---

## Implementation Overview

### Implementation Summary
<!-- AI: Summarize the implementation approach based on the design document -->
<!-- IMPORTANT: Clarify if this is a complete replacement or extension approach. For replacements, emphasize that NO legacy code will be preserved - only external API compatibility is maintained. -->

### Implementation Goals
<!-- AI: List the key implementation goals -->
- [Implementation goal 1]
- [Implementation goal 2]
- [Implementation goal 3]

### Implementation Strategy
<!-- AI: Specify if this is a complete replacement or extension approach -->
**CRITICAL**: Specify whether this is:
- **Complete Code Replacement**: Existing implementation will be entirely removed and replaced with new code (maintain only external API compatibility)
- **Extension/Enhancement**: Existing code will be extended or enhanced (maintain internal compatibility)

### Implementation Constraints
<!-- AI: List any implementation constraints -->
- Must maintain external API endpoint contracts without breaking changes (for UI and external integrations)
- [Internal implementation can be completely replaced if using complete replacement approach]
- [Constraint 2]
- [Constraint 3]

### Success Criteria
<!-- AI: Reference success criteria from requirements document -->
- [ ] [Success criterion 1 from requirements]
- [ ] [Success criterion 2 from requirements]
- [ ] [Success criterion 3 from requirements]

### Rollback Strategy
<!-- AI: Choose appropriate rollback strategy based on implementation approach -->
**For Complete Code Replacement:**
- Use git rollbacks to revert modified files to previous versions
- No legacy code preservation needed - clean rollback to working state
- Focus on external API compatibility during rollback testing

**For Extensions/Enhancements:**
- Use specific feature rollbacks while preserving existing functionality
- May require selective code removal rather than full file rollbacks

### Backward Compatibility Guidelines
**External API Compatibility (Always Required):**
- Maintain same REST endpoint paths, methods, and response formats
- Preserve WebSocket communication contracts
- Keep same configuration file formats (external)
- Maintain same command-line interfaces (if any)

**Internal Compatibility (NOT Required for Complete Replacements):**
- Internal class interfaces can be completely changed
- Internal method signatures can be completely different
- Internal data structures can be completely redesigned
- Internal configuration formats can be completely changed
- Legacy code does not need to be preserved or wrapped

## Phase 1: Foundation & Setup

### Phase 1 Overview
**Dependencies:** [List any dependencies]
**Goal:** [Overall goal for Phase 1]

#### Step 1.1: [Step Name]
**Goal:** [Specific goal for this step]
**Files to Create/Modify:**
- `path/to/file1.py` (new)
- `path/to/file2.py` (modify | completely replace if using replacement approach)
- `path/to/file3.py` (modify | completely replace if using replacement approach)

**AI Prompt:** `Implement Step 1.1 of EP-XXXX: [step description]`
<!-- For complete replacements, include phrases like "completely replace", "remove all legacy code", "no legacy preservation" -->

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]
- [ ] [Atomic task 3]

**Dependencies:**
- [Internal dependency 1]
- [External dependency 1]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]
- [ ] [Specific, testable criterion 3]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
[verification command 3]
```

#### Step 1.2: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (new)
- `path/to/file2.py` (modify)

**AI Prompt:** `Implement Step 1.2 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]
- [ ] [Atomic task 3]

**Dependencies:**
- [Step 1.1 must be complete]
- [Other dependency]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

#### Step 1.3: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (modify)
- `path/to/file2.py` (modify)

**AI Prompt:** `Implement Step 1.3 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Step 1.2 must be complete]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

### Phase 1 Completion Criteria
- [ ] [Overall Phase 1 success criterion 1]
- [ ] [Overall Phase 1 success criterion 2]
- [ ] [Overall Phase 1 success criterion 3]

## Phase 2: Core Implementation

### Phase 2 Overview
**Dependencies:** [Phase 1 completion]
**Goal:** [Overall goal for Phase 2]

#### Step 2.1: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (new)
- `path/to/file2.py` (modify)

**AI Prompt:** `Implement Step 2.1 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]
- [ ] [Atomic task 3]

**Dependencies:**
- [Phase 1 completion]
- [Specific dependency]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

#### Step 2.2: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (modify)
- `path/to/file2.py` (modify)

**AI Prompt:** `Implement Step 2.2 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Step 2.1 must be complete]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

#### Step 2.3: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (modify)
- `path/to/file2.py` (modify)

**AI Prompt:** `Implement Step 2.3 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Step 2.2 must be complete]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

### Phase 2 Completion Criteria
- [ ] [Overall Phase 2 success criterion 1]
- [ ] [Overall Phase 2 success criterion 2]
- [ ] [Overall Phase 2 success criterion 3]

## Phase 3: Integration & Testing

### Phase 3 Overview
**Dependencies:** [Phase 2 completion]
**Goal:** [Overall goal for Phase 3]

#### Step 3.1: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/test1.py` (new)
- `path/to/test2.py` (new)

**AI Prompt:** `Implement Step 3.1 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Phase 2 completion]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

#### Step 3.2: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (modify)
- `path/to/integration_test.py` (new)

**AI Prompt:** `Implement Step 3.2 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Step 3.1 must be complete]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

#### Step 3.3: [Step Name]
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/e2e_test.py` (new)
- `path/to/performance_test.py` (new)

**AI Prompt:** `Implement Step 3.3 of EP-XXXX: [step description]`

**Tasks:**
- [ ] [Atomic task 1]
- [ ] [Atomic task 2]

**Dependencies:**
- [Step 3.2 must be complete]

**Validation Criteria:**
- [ ] [Specific, testable criterion 1]
- [ ] [Specific, testable criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[verification command 1]
[verification command 2]
```

### Phase 3 Completion Criteria
- [ ] [Overall Phase 3 success criterion 1]
- [ ] [Overall Phase 3 success criterion 2]
- [ ] [Overall Phase 3 success criterion 3]

## Phase 4: Documentation & Finalization

### Phase 4 Overview
**Dependencies:** [Phase 3 completion]
**Goal:** [Overall goal for Phase 4]

#### Step 4.1: Code Documentation
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `path/to/file1.py` (modify - add docstrings)
- `path/to/file2.py` (modify - add docstrings)

**AI Prompt:** `Implement Step 4.1 of EP-XXXX: Code Documentation`

**Tasks:**
- [ ] [Documentation task 1]
- [ ] [Documentation task 2]

**Dependencies:**
- [Phase 3 completion]

**Validation Criteria:**
- [ ] [Documentation criterion 1]
- [ ] [Documentation criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[documentation verification command]
```

#### Step 4.2: Update Main Documentation
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `docs/requirements.md` (modify)
- `docs/design.md` (modify)

**AI Prompt:** `Implement Step 4.2 of EP-XXXX: Update Main Documentation`

**Tasks:**
- [ ] [Documentation task 1]
- [ ] [Documentation task 2]

**Dependencies:**
- [Step 4.1 must be complete]

**Validation Criteria:**
- [ ] [Documentation criterion 1]
- [ ] [Documentation criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[documentation verification command]
```

#### Step 4.3: Final Validation
**Goal:** [Specific goal for this step]

**Files to Create/Modify:**
- `docs/enhancements/implemented/EP-XXXX-requirements.md` (move)
- `docs/enhancements/implemented/EP-XXXX-design.md` (move)
- `docs/enhancements/implemented/EP-XXXX-implementation.md` (move)

**AI Prompt:** `Implement Step 4.3 of EP-XXXX: Final Validation`

**Tasks:**
- [ ] [Validation task 1]
- [ ] [Validation task 2]

**Dependencies:**
- [Step 4.2 must be complete]

**Validation Criteria:**
- [ ] [Final validation criterion 1]
- [ ] [Final validation criterion 2]

**Success Check:**
```bash
# Commands to verify this step
[final verification command]
```

### Phase 4 Completion Criteria
- [ ] [Overall Phase 4 success criterion 1]
- [ ] [Overall Phase 4 success criterion 2]
- [ ] [Overall Phase 4 success criterion 3]

## Testing Strategy

### Test Plans
<!-- AI: Reference test plans from design document -->

### Test Execution
<!-- AI: Describe how tests will be executed -->

#### Unit Tests
- [ ] [Unit test requirement 1]
- [ ] [Unit test requirement 2]
- [ ] [Unit test requirement 3]

#### Integration Tests  (Mock Services Only)
- [ ] [Integration test requirement 1]
- [ ] [Integration test requirement 2]
- [ ] [Integration test requirement 3]

#### End-to-End Tests (Mock Services Only)
- [ ] [End-to-End test requirement 1]
- [ ] [End-to-End test requirement 2]
- [ ] [End-to-End test requirement 3]

## Resource Requirements

### Technical Resources
<!-- AI: List technical resource requirements -->
- [Resource 1]: [Description and requirements]
- [Resource 2]: [Description and requirements]

### External Dependencies
<!-- AI: List external dependencies -->
- [Dependency 1]: [Description]
- [Dependency 2]: [Description]

## Documentation Updates Required

### Main Documentation Updates
<!-- AI: Reference documentation requirements from design document -->

#### requirements.md Updates
- [ ] **Section [X.X]**: [Specific change needed]
- [ ] **Section [X.X]**: [Specific change needed]
- [ ] **New Section**: [What needs to be added]

#### design.md Updates
- [ ] **Section [X.X]**: [Specific change needed]
- [ ] **Section [X.X]**: [Specific change needed]
- [ ] **New Section**: [What needs to be added]

#### Other Documentation
- [ ] [File/section]: [Change needed]
- [ ] [File/section]: [Change needed]

## Monitoring & Success Metrics

### Success Metrics
<!-- AI: Reference success criteria from requirements document -->
- [Metric 1]: [Target value]
- [Metric 2]: [Target value]
- [Metric 3]: [Target value]

---

## Implementation Checklist

### Pre-Implementation
- [ ] Requirements document approved
- [ ] Design document approved
- [ ] Implementation plan approved
- [ ] Resources allocated
- [ ] Dependencies confirmed

### During Implementation
- [ ] Follow step-by-step process
- [ ] Validate each step before proceeding
- [ ] Update progress regularly
- [ ] Escalate issues promptly
- [ ] Document decisions and changes

### Post-Implementation
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Success metrics achieved
- [ ] Stakeholders notified
- [ ] Implementation marked complete

---

## AI Implementation Guide

### Implementation Approach Reminder
**CRITICAL**: If this is a complete replacement implementation:
- Remove ALL legacy code - do not preserve, wrap, or extend existing implementation
- Focus ONLY on maintaining external API endpoint compatibility
- Use clear AI prompts like "completely replace" and "remove all legacy code"
- Internal implementation can be entirely different from original

### Step-by-Step Execution
1. **Implement each step individually** using the specific AI prompt
2. **Validate each step** using the success check commands
3. **Proceed only after validation** to avoid cascading failures
4. **Update progress** by checking off completed tasks
5. **Escalate issues** if validation fails

### Implementation Pattern
```
AI Prompt: "Implement Step X.Y of EP-XXXX: [step description]"
[For complete replacements, add: "Completely replace existing implementation. Remove all legacy code."]
Human: Run success check commands
Human: Verify validation criteria
Human: Check off completed tasks
Human: Proceed to next step only if all validation passes
```

### Troubleshooting
- If a step fails validation, use the appropriate rollback strategy (git revert for complete replacements)
- Review dependencies before proceeding
- Check for blockers and resolve them
- For complete replacements: Don't try to preserve failing code, revert cleanly and retry

---

## Completion Criteria

### Final Success Criteria
- [ ] [All requirements from requirements document are met]
- [ ] [All design elements from design document are implemented]
- [ ] [All test cases pass]
- [ ] [All documentation is updated]
- [ ] [All stakeholders are satisfied]

### Implementation Complete
When all phases are complete and all success criteria are met, this EP implementation is considered complete and can be moved to the implemented directory.

**Final AI Prompt:**
```
Review EP-XXXX implementation and mark it as completed. Move all three documents (requirements, design, implementation) to the implemented directory and update the EP registry.
``` 