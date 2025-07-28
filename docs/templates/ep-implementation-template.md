# EP-XXXX: [Title] - Implementation Guidelines

**Status:** Draft | Approved  
**Created:** [Use current date in YYYY-MM-DD format - AI should use tools to get current date]  
**Requirements:** `docs/enhancements/pending/EP-XXXX-requirements.md`
**Design:** `docs/enhancements/pending/EP-XXXX-design.md`

This document provides AI with the essential standards and processes for implementing EPs. Use this alongside the requirements and design documents to execute implementations effectively.

---

## Code Standards

### Code Quality Requirements
- **Docstrings**: Add to all new public functions, classes, and modules
- **Type Hints**: Use for all function parameters and return values
- **Error Handling**: Include meaningful error messages and proper exception types
- **Logging**: Use structured logging for debugging and monitoring

### Testing Approach
- **Comprehensive but Practical**: Test business logic, error conditions, integration points, and user workflows
- **Mock External Dependencies**: Don't rely on external services in tests
- **Balance Coverage vs Complexity**: Aim for thorough testing that's maintainable, not arbitrary coverage percentages
- **Test Error Cases**: Include edge cases, failure scenarios, and input validation
- **Test Integration**: Verify component interactions and data flow paths

### Validation Commands
Use appropriate commands based on implementation type:

**For Python/Backend Changes:**
```bash
# Run all tests
python -m pytest tests/ -v

# Check code style and quality
pre-commit run --all-files

# Type checking
mypy src/

# Run specific test categories
python -m pytest tests/unit/ -v          # Unit tests
python -m pytest tests/integration/ -v   # Integration tests
python -m pytest tests/api/ -v          # API compatibility tests
```

**For UI/Frontend Changes:**
```bash
# Run frontend tests
npm test

# Check code style and linting
npm run lint

# Type checking (if using TypeScript)
npm run type-check

# Build verification
npm run build

# End-to-end tests
npm run test:e2e
```

**For Mixed Backend/Frontend Changes:**
Use both sets of commands as applicable to the components being changed.

---

## Implementation Planning

### Breaking Down Complex Work
1. **Identify Dependencies**: What must be built before other parts can work
2. **Create Testable Chunks**: Each phase should be independently validatable
3. **Minimize Risk**: Implement core functionality first, extensions second
4. **Enable Early Validation**: Structure work so problems are caught quickly

### Phase Planning Strategy
**Adapt the number of phases based on complexity:**

**For Simple Changes (1-2 phases):**
- **Phase 1**: Implement change and basic tests
- **Phase 2**: Integration testing and validation

**For Moderate Changes (3-4 phases):**
- **Phase 1**: Core functionality
- **Phase 2**: Integration points  
- **Phase 3**: Error handling and edge cases
- **Phase 4**: Testing and validation

**For Complex Changes (4+ phases):**
- **Phase 1**: Foundation/data structures
- **Phase 2**: Core business logic
- **Phase 3**: API/integration layer
- **Phase 4**: Error handling and resilience
- **Phase 5+**: Additional phases as needed

### Implementation Order
1. **Data structures and core logic** (foundation)
2. **API endpoints or interfaces** (integration points)
3. **Error handling and validation** (robustness)
4. **Tests and documentation** (verification)

---

## Execution Process

### For Each Implementation Phase:
1. **Implement** the functionality for this phase
2. **Test** using the validation commands above
3. **Fix** any issues before proceeding
4. **Document** any important decisions or changes
5. **Move** to next phase only when current phase passes validation

### Quality Gates
Before marking any phase complete:
- [ ] All code follows the standards above
- [ ] All validation commands pass
- [ ] Tests cover the implemented functionality
- [ ] Error handling is appropriate
- [ ] Integration points work as expected

### When Things Go Wrong
- **Test Failures**: Check mocking setup and test logic
- **Type Errors**: Add missing type annotations
- **Import Issues**: Verify module structure and dependencies
- **Integration Problems**: Check API contracts and data formats

---

## Definition of Done

An EP implementation is complete when:
- [ ] All requirements from the requirements document are met
- [ ] All design elements from the design document are implemented
- [ ] All validation commands pass consistently
- [ ] Critical functionality has appropriate test coverage
- [ ] Code includes proper documentation and error handling
- [ ] Integration points work as specified in the design
- [ ] Implementation is ready for production use

---

## AI Implementation Notes

### Reading the Design Document
- Understand the implementation strategy (replace/extend/new)
- Identify which components need changes
- Note compatibility requirements and constraints
- Plan phases based on dependencies and complexity

### Creating Implementation Plans
- **Choose appropriate number of phases** based on EP complexity
- Break work into **logical, testable chunks** that make sense for the specific change
- Specify exact files to modify in each phase
- Include validation steps for each phase
- Order phases to minimize risk and enable early testing

### During Implementation
- Follow the code standards consistently
- Run validation commands after each significant change
- Test thoroughly before moving to the next phase
- Document any deviations from the original design 