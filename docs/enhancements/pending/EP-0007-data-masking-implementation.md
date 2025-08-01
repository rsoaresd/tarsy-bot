# EP-0007: Data Masking Service for Sensitive MCP Server Data - Implementation Guidelines

**Status:** Draft  
**Created:** 2025-07-31  
**Requirements:** `docs/enhancements/pending/EP-0007-data-masking-requirements.md`
**Design:** `docs/enhancements/pending/EP-0007-data-masking-design.md`

This document provides the implementation plan for adding data masking capabilities to prevent sensitive MCP server data from reaching the LLM, logging, and storage systems.

---

## Implementation Planning

### Complexity Assessment
**Moderate-Complex Change (5 phases)**

This implementation involves:
- **New service creation**: DataMaskingService with pattern matching
- **Data model additions**: MaskingConfig and MaskingPattern models
- **Integration point modification**: MCPClient.call_tool() method
- **Configuration system extension**: Built-in and YAML configuration support
- **Pattern system**: Built-in patterns, pattern groups, and custom patterns

### Dependencies Analysis
1. **Foundation First**: Data models and core masking service must exist before integration
2. **Integration Layer**: MCPClient integration depends on core service completion
3. **Configuration Loading**: Requires both data models and service to be functional
4. **Testing Validation**: All components must be implemented for end-to-end testing

---

## Phase Breakdown

### Phase 1: Foundation - Core Data Models
**Focus**: Establish data structures and basic masking service skeleton

**Files to Create:**
- `backend/tarsy/models/masking_config.py`
- `backend/tarsy/services/data_masking_service.py` (basic structure)

**Implementation Tasks:**
1. **Create MaskingPattern data model** with validation
   - `name`, `pattern`, `replacement`, `description`, `enabled` fields
   - Pydantic validation for regex pattern syntax
   - Type hints and docstrings

2. **Create MaskingConfig data model** with validation
   - `enabled`, `pattern_groups`, `patterns`, `custom_patterns` fields
   - Validation for pattern group names and pattern lists
   - Type hints and docstrings

3. **Create DataMaskingService skeleton**
   - Constructor with MCPServerRegistry dependency
   - Built-in pattern constants (BUILTIN_MASKING_PATTERNS, BUILTIN_PATTERN_GROUPS)
   - Method signatures for `mask_response()`, `_apply_patterns()`, pattern compilation
   - No actual masking logic yet - just structure

**Validation:**
```bash
# Type checking
mypy backend/tarsy/models/masking_config.py
mypy backend/tarsy/services/data_masking_service.py

# Run basic import tests
python -c "from tarsy.models.masking_config import MaskingConfig, MaskingPattern; print('Import successful')"
python -c "from tarsy.services.data_masking_service import DataMaskingService; print('Import successful')"
```

**Success Criteria:**
- [ ] All data models pass type checking
- [ ] Models can be imported without errors
- [ ] Basic Pydantic validation works for config models
- [ ] DataMaskingService can be instantiated (with mock registry)

### Phase 2: Core Business Logic - Pattern Matching Implementation
**Focus**: Implement the actual masking functionality

**Files to Modify:**
- `backend/tarsy/services/data_masking_service.py`

**Implementation Tasks:**
1. **Implement pattern compilation system**
   - Load and compile built-in regex patterns at initialization
   - Validate regex patterns and handle compilation errors
   - Create pattern group expansion logic

2. **Implement core masking logic**
   - `mask_response()` method with server-specific configuration lookup
   - `_apply_patterns()` method with regex matching and replacement
   - JSON/dict traversal to mask nested response content
   - Preserve response structure while masking string values

3. **Add basic error handling**
   - Pattern compilation error handling (disable problematic patterns)
   - Masking processing error handling (fail-safe behavior)
   - Logging for debugging and monitoring

**Validation:**
```bash
# Unit tests for core masking logic
python -m pytest tests/unit/services/test_data_masking_service.py -v

# Type checking
mypy backend/tarsy/services/data_masking_service.py

# Manual testing with sample data
python -c "
from tarsy.services.data_masking_service import DataMaskingService
from unittest.mock import Mock
registry = Mock()
service = DataMaskingService(registry)
print('Core service functional')
"
```

**Success Criteria:**
- [ ] Built-in patterns compile successfully
- [ ] Pattern matching works on sample text
- [ ] Response structure is preserved during masking
- [ ] Fail-safe behavior triggers on errors
- [ ] Unit tests pass for core masking logic

### Phase 3: Integration Layer - MCPClient Integration
**Focus**: Integrate masking service into the MCP data flow

**Files to Modify:**
- `backend/tarsy/integrations/mcp/client.py`
- `backend/tarsy/models/mcp_config.py`

**Implementation Tasks:**
1. **Extend MCPServerConfig model**
   - Add `data_masking: Optional[MaskingConfig]` field
   - Ensure backward compatibility (optional field)
   - Update model validation and type hints

2. **Integrate DataMaskingService into MCPClient**
   - Add masking service dependency injection in constructor
   - Modify `call_tool()` method to apply masking before response return
   - Handle cases where masking service is None (backward compatibility)
   - Preserve existing error handling and logging flow

3. **Add configuration lookup logic**
   - Query MCPServerRegistry for server-specific masking config
   - Handle missing or disabled masking configurations gracefully

**Validation:**
```bash
# Integration tests
python -m pytest tests/integration/test_mcp_client_masking.py -v

# Type checking
mypy backend/tarsy/integrations/mcp/client.py
mypy backend/tarsy/models/mcp_config.py

# Test MCPClient with masking enabled
python -m pytest tests/unit/integrations/test_mcp_client.py -v
```

**Success Criteria:**
- [ ] MCPClient can be initialized with DataMaskingService
- [ ] `call_tool()` method applies masking when configured
- [ ] Response format unchanged for external APIs
- [ ] Backward compatibility maintained (no masking service = no masking)
- [ ] Integration tests pass

### Phase 4: Configuration System - Built-in and YAML Support
**Focus**: Enable configuration-driven masking patterns

**Files to Modify:**
- `backend/tarsy/config/builtin_config.py`
- `backend/tarsy/models/agent_config.py`
- `backend/tarsy/services/mcp_server_registry.py`
- `config/agents.yaml.example`

**Implementation Tasks:**
1. **Add built-in server masking configuration**
   - Update `BUILTIN_MCP_SERVERS` with masking config for kubernetes-server
   - Use pattern groups and individual patterns as designed
   - Ensure proper integration with existing server definitions

2. **Extend agent configuration models**
   - Add masking config support to `MCPServerConfigModel` for YAML loading
   - Ensure validation and type checking for YAML-defined masking configs
   - Handle custom patterns in YAML configuration

3. **Update configuration template**
   - Add comprehensive masking examples to `agents.yaml.example`
   - Show pattern groups, individual patterns, and custom patterns usage
   - Include different server types with various masking approaches

4. **Integrate configuration loading**
   - Ensure MCPServerRegistry loads masking configs from both sources
   - Test configuration precedence and validation
   - Handle configuration errors gracefully

5. **Ensure MCPServerRegistry integration**
   - Verify masking configs are properly loaded from both built-in and YAML sources
   - Test configuration lookup and retrieval through registry methods
   - Validate masking config integration with existing server setup flow

**Validation:**
```bash
# Configuration loading tests
python -m pytest tests/unit/config/test_builtin_config.py -v
python -m pytest tests/unit/models/test_agent_config.py -v
python -m pytest tests/unit/services/test_mcp_server_registry.py -v

# YAML configuration validation
python -c "
from tarsy.config.configuration_loader import ConfigurationLoader
loader = ConfigurationLoader('config/agents.yaml.example')
config = loader.load_configuration()
print('YAML config loads successfully')
"

# Type checking
mypy backend/tarsy/config/builtin_config.py
mypy backend/tarsy/models/agent_config.py
mypy backend/tarsy/services/mcp_server_registry.py
```

**Success Criteria:**
- [ ] Built-in servers load with masking configuration
- [ ] YAML configuration supports all masking features
- [ ] Custom patterns can be defined and loaded from YAML
- [ ] Configuration validation prevents invalid setups
- [ ] MCPServerRegistry properly loads and provides masking configs
- [ ] Both built-in and configured servers work with masking

### Phase 5: Testing and Validation - End-to-End Functionality
**Focus**: Comprehensive testing and final validation

**Files to Create:**
- `tests/unit/services/test_data_masking_service.py`
- `tests/integration/test_mcp_client_masking.py`
- `tests/unit/models/test_masking_config.py`
- `tests/unit/services/test_mcp_server_registry_masking.py`

**Implementation Tasks:**
1. **Create comprehensive unit tests**
   - DataMaskingService pattern matching tests
   - MaskingConfig and MaskingPattern validation tests
   - Error handling and fail-safe behavior tests
   - Pattern group expansion and custom pattern tests
   - MCPServerRegistry masking config loading and retrieval tests

2. **Create integration tests**
   - End-to-end MCP call with masking enabled
   - Configuration loading and application tests
   - Multiple server types with different masking configs
   - Error scenarios and edge cases

3. **Validate performance and security**
   - Test masking performance on large responses
   - Validate regex patterns for ReDoS protection
   - Ensure fail-safe behavior in all error conditions
   - Test pattern bypass attempts

4. **Documentation and examples**
   - Update docstrings with comprehensive examples
   - Validate all code examples in design document
   - Test configuration examples in `agents.yaml.example`

**Validation:**
```bash
# Run all tests
python -m pytest tests/ -v

# Code quality checks
pre-commit run --all-files

# Type checking across all modified files
mypy backend/tarsy/

# Performance testing
python -m pytest tests/performance/test_masking_performance.py -v

# Security validation
python -m pytest tests/security/test_masking_security.py -v
```

**Success Criteria:**
- [ ] All unit tests pass with good coverage
- [ ] All integration tests pass
- [ ] Performance requirements met (reasonable overhead)
- [ ] Security validation passes (no pattern bypass, fail-safe works)
- [ ] All code quality checks pass
- [ ] Documentation is complete and accurate

---

## Code Standards

### Code Quality Requirements
- **Docstrings**: All public methods in DataMaskingService and data models
- **Type Hints**: Complete type annotations for all functions and class attributes
- **Error Handling**: Comprehensive error handling with meaningful messages and fail-safe behavior
- **Logging**: Structured logging for debugging, security events, and performance monitoring

### Testing Approach
- **Comprehensive Coverage**: Test business logic, error conditions, integration points, and security scenarios
- **Mock External Dependencies**: Use mocks for MCPServerRegistry and external MCP servers
- **Security Focus**: Test pattern bypass attempts, ReDoS protection, and fail-safe behavior
- **Performance Testing**: Validate reasonable overhead on typical MCP responses
- **Configuration Testing**: Test all configuration combinations and validation scenarios

---

## Risk Mitigation

### High Risk Areas
1. **Regex Performance**: Large responses could cause performance issues
   - **Mitigation**: Simple timeout protection and pattern optimization
   - **Testing**: Performance tests with large responses

2. **Pattern Bypass**: Sensitive data might not match patterns
   - **Mitigation**: Comprehensive pattern testing and fail-safe behavior
   - **Testing**: Security tests with bypass attempts

3. **Integration Breaking**: Changes to MCPClient could break existing functionality
   - **Mitigation**: Extensive integration testing and backward compatibility
   - **Testing**: Full MCP flow testing with and without masking

### Quality Gates
Before marking each phase complete:
- [ ] All validation commands pass
- [ ] Phase-specific success criteria met
- [ ] No regressions in existing functionality
- [ ] Code follows all quality standards
- [ ] Integration points work as expected

---

## Definition of Done

EP-0007 implementation is complete when:
- [ ] All requirements from EP-0007-data-masking-requirements.md are met
- [ ] All design elements from EP-0007-data-masking-design.md are implemented
- [ ] All validation commands pass consistently
- [ ] Comprehensive test coverage for masking functionality
- [ ] Security validation passes (fail-safe behavior, pattern effectiveness)
- [ ] Performance requirements met (reasonable overhead)
- [ ] Configuration system supports built-in and custom patterns
- [ ] Integration with MCPClient is seamless and backward compatible
- [ ] Implementation is ready for production use with sensitive MCP data

---

## Implementation Notes

### Critical Success Factors
1. **Fail-Safe Design**: Always err on the side of over-masking rather than under-masking
2. **Backward Compatibility**: Existing MCP flows must work unchanged when masking is disabled
3. **Performance Awareness**: Masking should not significantly impact MCP response times
4. **Configuration Flexibility**: Support both simple (pattern groups) and complex (custom patterns) use cases
5. **Security First**: Patterns must be effective and resistant to bypass attempts

### Execution Order Rationale
- **Phase 1-2**: Build solid foundation before integration complexity
- **Phase 3**: Integrate when core functionality is proven
- **Phase 4**: Add configuration complexity after integration is stable
- **Phase 5**: Comprehensive validation ensures production readiness

This phased approach minimizes risk by validating each component independently before combining them into the complete solution.