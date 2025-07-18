# AI Workflow Guide - Enhancement Proposals

This guide demonstrates how to use the Enhancement Proposal (EP) system with AI for iterative development of the SRE AI Agent.

## Quick Start

### 1. Create a New Enhancement Proposal

**Human Input:**
```
I want to improve the WebSocket connection handling to be more resilient and support connection pooling.
```

**AI Prompt:**
```
Generate an Enhancement Proposal using the template at docs/templates/enhancement-proposal-template.md for improving WebSocket connection handling with resilience and connection pooling. Use EP-0001 as the number and save it as docs/enhancements/pending/EP-0001-websocket-connection-improvements.md
```

### 2. Review and Refine

**Human Review:**
- Check technical accuracy
- Validate requirements impact
- Adjust implementation phases
- Add missing considerations

**AI Refinement Prompt:**
```
Update EP-0001 based on this feedback: [your feedback here]
```

### 3. Implement Step by Step

**Step-by-Step Implementation:**
```
Implement Step 1.1 of EP-0001: Initial Setup
```

**Validation After Each Step:**
```
# Run the success check commands from the EP
# Verify all validation criteria are met
# Only proceed to next step if all validations pass
```

**Continue with Next Step:**
```
Implement Step 1.2 of EP-0001: Core Implementation
```

**Repeat Pattern:**
- Implement step
- Validate step
- Proceed to next step only if current step is complete

### 4. Update Documentation

**Final Documentation Update:**
```
Update the main documentation files (requirements.md and design.md) according to EP-0001 documentation requirements. Show me the specific changes needed.
```

## Example Workflow

### Scenario: Adding Database Integration

**Step 1: Initial Request**
```
Human: I want to add database integration to persist alert processing history and system metrics.
```

**Step 2: Generate EP**
```
AI Prompt: Generate an Enhancement Proposal using the template at docs/templates/enhancement-proposal-template.md for adding database integration to persist alert processing history and system metrics. Use the next available EP number and save it as docs/enhancements/pending/EP-XXXX-database-integration.md
```

**Step 3: Review Generated EP**
```
Human: Reviews the generated EP and provides feedback:
- Use PostgreSQL instead of SQLite
- Add data retention policies
- Include database migration strategy
```

**Step 4: Refine EP**
```
AI Prompt: Update the database integration EP based on this feedback:
- Use PostgreSQL instead of SQLite
- Add data retention policies  
- Include database migration strategy
```

**Step 5: Implement Step 1.1**
```
AI Prompt: Implement Step 1.1 of EP-XXXX: Initial Setup
```

**Step 6: Validate Step 1.1**
```
# Run success check commands from the EP
# Verify validation criteria are met
# Confirm step is complete before proceeding
```

**Step 7: Implement Step 1.2**
```
AI Prompt: Implement Step 1.2 of EP-XXXX: Core Implementation
```

**Step 8: Validate Step 1.2**
```
# Run success check commands from the EP
# Verify validation criteria are met
# Confirm step is complete before proceeding
```

**Step 9: Continue with remaining steps**
```
AI Prompt: Implement Step 1.3 of EP-XXXX: Basic Testing
# Validate before proceeding to Phase 2

AI Prompt: Implement Step 2.1 of EP-XXXX: System Integration
# Validate before proceeding to Step 2.2

# Continue this pattern for all steps...
```

**Step 8: Update Documentation**
```
AI Prompt: Update the main documentation files according to the database integration EP documentation requirements. Show me the specific changes needed for requirements.md and design.md.
```

**Step 9: Complete EP**
```
AI Prompt: Review the database integration EP implementation and mark it as completed. Move it to the implemented directory and update the registry in docs/enhancements/README.md.
```

## AI Prompts Cheat Sheet

### Creating EPs
```
Generate an Enhancement Proposal using the template at docs/templates/enhancement-proposal-template.md for [specific request]. Use EP-XXXX as the number.
```

### Refining EPs
```
Update EP-XXXX based on this feedback: [feedback]
```

### Implementation (Step-by-Step)
```
Implement Step [X.Y] of EP-XXXX: [step description]
```

### Validation (After Each Step)
```
# Run success check commands from EP-XXXX Step [X.Y]
# Verify validation criteria are met
# Confirm step completion before proceeding
```

### Next Step
```
Implement Step [X.Y+1] of EP-XXXX: [next step description]
```

### Documentation Updates
```
Update the main documentation files according to EP-XXXX documentation requirements.
```

### Completion
```
Review EP-XXXX implementation and mark it as completed. Move it to the implemented directory.
```

## Benefits of Granular Step-by-Step Implementation

### 1. **Reduced Complexity**
- Each step is small and focused
- AI can handle atomic tasks more effectively
- Less chance of confusion or errors

### 2. **Better Validation**
- Specific success criteria for each step
- Immediate feedback on progress
- Early detection of issues

### 3. **Easier Debugging**
- Know exactly which step failed
- Clear rollback points
- Isolated problem areas

### 4. **Progress Tracking**
- Clear milestone markers
- Visual progress indicators
- Predictable completion times

### 5. **AI-Friendly Structure**
- Specific prompts for each step
- Clear file targets
- Atomic task descriptions

## Tips for Effective AI Collaboration

### 1. Be Specific in Requests
❌ **Bad:** "Improve the system"
✅ **Good:** "Improve WebSocket connection handling with automatic reconnection and connection pooling"

### 2. Provide Context
✅ **Include:** Current limitations, business requirements, technical constraints

### 3. Review Each Step (Not Just Phases)
✅ **Always:** Review AI-generated content for each step before proceeding

### 4. Iterate in Small Steps
✅ **Prefer:** Granular steps over large, complex tasks

### 5. Validate Continuously
✅ **Test:** Each step before moving to the next

### 6. Use Exact Prompts
✅ **Follow:** The specific AI prompts defined in each step

### 7. Verify File Lists
✅ **Check:** That AI is modifying the correct files as specified in each step

## Common Workflows

### 1. Performance Optimization
```
1. Generate EP for specific performance issue
2. Phase 1: Profiling and measurement
3. Phase 2: Implementation of optimizations
4. Phase 3: Validation and documentation
```

### 2. New Feature Addition
```
1. Generate EP with requirements analysis
2. Phase 1: Core functionality
3. Phase 2: Integration and testing
4. Phase 3: Documentation and examples
```

### 3. Architecture Refactoring
```
1. Generate EP with current state analysis
2. Phase 1: Preparation and compatibility
3. Phase 2: Incremental migration
4. Phase 3: Cleanup and optimization
```

### 4. Security Enhancement
```
1. Generate EP with security analysis
2. Phase 1: Risk assessment and planning
3. Phase 2: Implementation of security measures
4. Phase 3: Testing and validation
```

## Troubleshooting

### EP Generation Issues
- **Issue:** AI generates incomplete EP
- **Solution:** Provide more specific requirements and context

### Implementation Problems
- **Issue:** AI suggests incorrect implementation
- **Solution:** Review and provide corrective feedback, iterate

### Documentation Sync Issues
- **Issue:** Main docs not updated properly
- **Solution:** Use specific prompts for documentation updates

### Phase Dependency Issues
- **Issue:** Later phases depend on incomplete earlier phases
- **Solution:** Ensure each phase is fully validated before proceeding

## Best Practices

1. **Start Small:** Begin with focused, well-defined enhancements
2. **Iterate Often:** Prefer multiple small EPs over one large EP
3. **Validate Early:** Test each phase thoroughly
4. **Document Changes:** Keep main documentation current
5. **Review Regularly:** Human oversight is crucial for quality
6. **Use Templates:** Leverage the structured EP template
7. **Track Progress:** Update EP status regularly 