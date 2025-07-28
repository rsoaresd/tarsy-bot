# Tarsy-bot - Enhancement Proposals

This directory contains Enhancement Proposals (EPs) for the tarsy-bot project. Enhancement Proposals are used to document, design, and track significant changes to the system in an AI-friendly, iterative manner.

## Directory Structure

```
docs/
├── requirements.md          # Main requirements document (living)
├── design.md                # Main architecture document (living)
├── templates/
│   ├── ep-requirements-template.md    # Requirements phase template
│   ├── ep-design-template.md          # Design phase template
│   └── ep-implementation-template.md  # Implementation phase template
└── enhancements/
    ├── README.md            # This file
    ├── pending/             # Proposals in progress
    │   ├── EP-0001-requirements.md    # Requirements document
    │   ├── EP-0001-design.md          # Design document
    │   ├── EP-0001-implementation.md  # Implementation plan
    │   ├── EP-0002-requirements.md    # Next enhancement
    │   └── EP-0002-design.md          # (if approved)
    ├── approved/            # Approved but not implemented
    │   ├── EP-0003-requirements.md    # Approved requirements
    │   ├── EP-0003-design.md          # Approved design
    │   └── EP-0003-implementation.md  # Approved implementation plan
    └── implemented/         # Completed proposals
        ├── EP-0000-requirements.md    # Historical record
        ├── EP-0000-design.md          # Historical record
        └── EP-0000-implementation.md  # Historical record
```

## Enhancement Proposal Lifecycle

### Phase 1: Requirements Definition
1. **Create Requirements** → Use `ep-requirements-template.md` to define what needs to be built
2. **Review Requirements** → Human review and AI refinement of requirements
3. **Approve Requirements** → Requirements approved and ready for design

### Phase 2: Technical Design
1. **Create Design** → Use `ep-design-template.md` to design the technical solution
2. **Review Design** → Human review and AI refinement of design
3. **Approve Design** → Design approved and ready for implementation planning

### Phase 3: Implementation Planning & Execution
1. **Create Implementation Plan** → Use `ep-implementation-template.md` to create step-by-step plan
2. **Review Implementation Plan** → Human review and AI refinement of plan
3. **Approve Implementation Plan** → Plan approved and ready for execution
4. **Execute Implementation** → Follow step-by-step implementation with AI assistance
5. **Complete Implementation** → Move all three documents to `implemented/` directory

## AI-Friendly Workflow

### Creating a New Enhancement Proposal

#### Phase 1: Requirements Definition
1. **Generate Requirements**: Use the requirements template with AI
   ```
   AI Prompt: "Generate requirements using the template at docs/templates/ep-requirements-template.md for [specific enhancement request]. Save it as docs/enhancements/pending/EP-XXXX-requirements.md"
   ```

2. **Review and Refine Requirements**: Human review and AI refinement
   ```
   AI Prompt: "Update EP-XXXX requirements based on this feedback: [feedback]"
   ```

#### Phase 2: Technical Design
3. **Generate Design**: Use the design template with AI
   ```
   AI Prompt: "Create a design document using the template at docs/templates/ep-design-template.md for EP-XXXX based on the approved requirements in EP-XXXX-requirements.md"
   ```

4. **Review and Refine Design**: Human review and AI refinement
   ```
   AI Prompt: "Update EP-XXXX design based on this feedback: [feedback]"
   ```

#### Phase 3: Implementation Planning & Execution
5. **Generate Implementation Plan**: Use the implementation template with AI
   ```
   AI Prompt: "Create an implementation plan using the template at docs/templates/ep-implementation-template.md for EP-XXXX based on the approved requirements and design documents"
   ```

6. **Review and Refine Implementation Plan**: Human review and AI refinement
   ```
   AI Prompt: "Update EP-XXXX implementation plan based on this feedback: [feedback]"
   ```

7. **Execute Implementation**: Step-by-step implementation with AI
   ```
   AI Prompt: "Implement Step X.Y of EP-XXXX: [step description]"
   ```

8. **Update Main Documentation**: Update main documentation
   ```
   AI Prompt: "Update the main documentation files according to EP-XXXX documentation requirements."
   ```

## Enhancement Proposal Registry

### Pending Proposals
*EPs currently being developed or reviewed*

| EP # | Title | Phase | Status | Created | Priority |
|------|-------|--------|---------|----------|----------|
| EP-0001 | WebSocket Connection Improvements | Requirements | Draft | 2024-01-15 | Medium |

### Approved Proposals
*EPs approved for implementation*

| EP # | Title | Phase | Status | Created | Priority |
|------|-------|--------|---------|----------|----------|
| -    | -     | -      | -       | -        | -        |

### Implemented Proposals
*EPs that have been successfully implemented*

| EP # | Title | Implemented | Requirements Updated | Design Updated |
|------|-------|-------------|----------------------|----------------|
| EP-0002 | Multi-Layer Agent Design | 2025-07-20 | ✅ | ✅ |
| EP-0003 | Alert Processing History | 2025-07-25 | ✅ | ✅ |
| EP-0004 | Dashboard UI for Alert History | 2025-07-27 | ✅ | ✅ |

## Naming Convention

- **Format**: `EP-XXXX-brief-descriptive-title.md`
- **Example**: `EP-0001-websocket-connection-improvements.md`
- **Numbering**: 4-digit sequential numbering (0001, 0002, etc.)

## AI Prompts for Common Tasks

### Generate Requirements
```
Generate requirements using the template at docs/templates/ep-requirements-template.md for [specific enhancement request]. Use the next available EP number and save it as docs/enhancements/pending/EP-XXXX-requirements.md
```

### Generate Design
```
Create a design document using the template at docs/templates/ep-design-template.md for EP-XXXX based on the approved requirements in EP-XXXX-requirements.md
```

### Generate Implementation Plan
```
Create an implementation plan using the template at docs/templates/ep-implementation-template.md for EP-XXXX based on the approved requirements and design documents
```

### Execute Implementation Step by Step
```
Implement Step [X.Y] of EP-XXXX: [step description]
```

### Validate Each Step
```
# Run success check commands from EP-XXXX Step [X.Y]
# Verify validation criteria are met
# Confirm step completion before proceeding
```

### Update Documentation
```
Update the main documentation files (requirements.md and design.md) according to EP-XXXX documentation requirements. Show me the specific changes needed.
```

### Complete EP
```
Review EP-XXXX implementation and mark it as completed. Move all three documents (requirements, design, implementation) to the implemented directory and update the registry.
```

## Integration with Main Documentation

Enhancement Proposals are designed to integrate seamlessly with the main documentation:

- **requirements.md**: Updated with new/modified requirements from EPs
- **design.md**: Updated with architectural changes from EPs
- **Cross-references**: Main docs reference relevant EPs for context

## Best Practices

1. **Start with Problem**: Always begin with a clear problem statement
2. **AI-Friendly Structure**: Use structured sections with clear prompts
3. **Iterative Development**: Implement in phases with validation
4. **Documentation First**: Update docs as part of implementation
5. **Track Progress**: Use checkboxes and status updates
6. **Validate Success**: Define clear success criteria

## Example Enhancement Proposal

See the templates for complete examples with AI-friendly prompts and structured sections:
- `docs/templates/ep-requirements-template.md` - Requirements definition template
- `docs/templates/ep-design-template.md` - Technical design template  
- `docs/templates/ep-implementation-template.md` - Implementation plan template

## Questions or Issues?

If you encounter issues with the Enhancement Proposal process, consider:
1. Reviewing the template for clarity
2. Checking the AI prompts for completeness
3. Ensuring proper directory structure
4. Validating numbering sequence 