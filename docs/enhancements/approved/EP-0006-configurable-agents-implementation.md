# EP-0006: Configuration-Based Agents - Implementation Guidelines

**Status:** Approved  
**Created:** 2025-07-29  
**Requirements:** `docs/enhancements/approved/EP-0006-configurable-agents-requirements.md`
**Design:** `docs/enhancements/approved/EP-0006-configurable-agents-design.md`

This document provides implementation guidelines for EP-0006: Configuration-Based Agents. This enhancement allows defining agents and MCP servers through YAML configuration files while maintaining full backward compatibility with existing hardcoded agents.

---

## Code Standards

### Code Quality Requirements
- **Docstrings**: Add to all new public functions, classes, and modules with clear parameter and return value descriptions
- **Type Hints**: Use comprehensive type hints for all function parameters, return values, and class attributes
- **Error Handling**: Include meaningful error messages with specific failure details and proper exception types (ConfigurationError)
- **Logging**: Use structured logging for configuration loading, validation failures, and agent creation

### Testing Approach
- **Comprehensive but Practical**: Test configuration loading, validation logic, agent creation, and error conditions
- **Mock External Dependencies**: Mock file system access, YAML parsing, and external services
- **Balance Coverage vs Complexity**: Focus on critical business logic: configuration parsing, conflict detection, agent instantiation
- **Test Error Cases**: Invalid YAML, missing files, naming conflicts, invalid MCP server references
- **Test Integration**: Verify registry population, agent factory creation, and end-to-end configuration flow

### Validation Commands

**For This Implementation:**
```bash
# Run all tests
python -m pytest tests/ -v

# Check code style and quality
pre-commit run --all-files

# Type checking
mypy backend/tarsy/

# Run specific test categories
python -m pytest tests/unit/models/ -v              # Configuration models
python -m pytest tests/unit/config/ -v             # Configuration loading
python -m pytest tests/unit/agents/ -v             # Agent implementations
python -m pytest tests/unit/services/ -v           # Registry extensions
python -m pytest tests/integration/ -v             # End-to-end integration

# Test configuration examples
python -c "from tarsy.config.agent_config import ConfigurationLoader; loader = ConfigurationLoader('./config/agents.yaml.example'); config = loader.load_and_validate(); print('Config validation passed')"
```

---

## Implementation Planning

### Breaking Down Complex Work

This is a **complex change** involving new components, existing component extensions, and comprehensive validation logic. The implementation follows these dependencies:

1. **Foundation First**: Configuration models and basic loading must exist before anything else
2. **Core Logic Second**: Agent and validation logic depends on foundation
3. **Integration Third**: Registry and factory extensions depend on core logic
4. **Validation Last**: Comprehensive testing and error handling validate the complete system

### Phase Planning Strategy

**Complex Changes (5 phases) - Chosen based on:**
- Multiple new components and existing component extensions
- Complex validation and conflict detection logic
- Integration points across multiple services
- Need for comprehensive error handling and testing

---

## Implementation Phases

### Phase 1: Foundation and Data Structures

**Objective**: Create the foundational data models and configuration structure

**Files to Create:**
- `backend/tarsy/models/agent_config.py` - Pydantic models for configuration validation
- `config/agents.yaml.example` - Example configuration file template

**Files to Modify:**
- `backend/tarsy/config/settings.py` - Add `agent_config_path` setting with environment variable support
- `backend/env.template` - Add `AGENT_CONFIG_PATH` example

**Key Tasks:**
1. **Create Pydantic Models**:
   - `AgentConfigModel` with `alert_types`, `mcp_servers`, `custom_instructions`
   - `MCPServerConfigModel` with `server_id`, `server_type`, `enabled`, `connection_params`, `instructions`
   - `CombinedConfigModel` with `agents` and `mcp_servers` dictionaries
   - Add comprehensive field validation and documentation

2. **Extend Settings**:
   - Add `agent_config_path: str = Field(default="./config/agents.yaml", description="Path to agent and MCP server configuration file")`
   - Ensure Pydantic automatically maps `AGENT_CONFIG_PATH` environment variable

3. **Create Example Configuration**:
   - Add example agents with different `alert_types` and `mcp_servers`
   - Show mixed usage of built-in and configured MCP servers
   - Include comprehensive comments explaining each field

**Validation Steps:**
```bash
# Test Pydantic model validation
python -c "from tarsy.models.agent_config import AgentConfigModel, MCPServerConfigModel, CombinedConfigModel; print('Models imported successfully')"

# Test settings extension
python -c "from tarsy.config.settings import get_settings; settings = get_settings(); print(f'Agent config path: {settings.agent_config_path}')"

# Validate example configuration file exists and has basic structure
ls -la config/agents.yaml.example
echo "Example configuration created successfully"
```

**Success Criteria:**
- [ ] All Pydantic models validate correctly with proper error messages
- [ ] Settings include `agent_config_path` with environment variable support
- [ ] Example configuration file has comprehensive examples and documentation
- [ ] All validation commands pass

---

### Phase 2: Core Business Logic

**Objective**: Implement configuration loading, validation, and the configurable agent class

**Files to Create:**
- `backend/tarsy/config/agent_config.py` - ConfigurationLoader with comprehensive validation and conflict detection
- `backend/tarsy/agents/configurable_agent.py` - ConfigurableAgent extending BaseAgent

**Key Tasks:**
1. **Implement ConfigurationLoader**:
   - `load_and_validate()` method with file existence checking, YAML parsing, Pydantic validation
   - `_validate_mcp_server_references()` - ensure all agent MCP server references exist in unified built-in + configured registry
   - `_detect_conflicts()` - check for naming conflicts (configured vs built-in names) and alert type conflicts (multiple agents per alert type)
   - Built-in constants injection from existing registries
   - Comprehensive error handling with `ConfigurationError` exceptions

2. **Implement ConfigurableAgent**:
   - Extend `BaseAgent` with proper dependency injection
   - Override `mcp_servers()` to return configuration-specified servers
   - Override `custom_instructions()` to return configuration-specified instructions
   - Maintain full compatibility with BaseAgent's processing logic and prompt building

3. **Error Handling Strategy**:
   - Missing files: graceful fallback (return empty configuration)
   - Malformed YAML: fail-fast with technical error details
   - Invalid configuration: fail-fast with Pydantic validation errors
   - MCP server reference errors: fail-fast with specific missing server details
   - Conflict errors: fail-fast with specific conflict details

**Validation Steps:**
```bash
# Test configuration loader with missing file (should return empty config)
python -c "from tarsy.config.agent_config import ConfigurationLoader; loader = ConfigurationLoader('nonexistent.yaml'); config = loader.load_and_validate(); print(f'Missing file handled correctly: {len(config.agents)} agents, {len(config.mcp_servers)} servers')"

# Test configuration loader with example file
python -c "from tarsy.config.agent_config import ConfigurationLoader; loader = ConfigurationLoader('./config/agents.yaml.example'); config = loader.load_and_validate(); print(f'Loaded {len(config.agents)} agents and {len(config.mcp_servers)} MCP servers')"

# Test ConfigurableAgent import (full instantiation requires mocked dependencies)
python -c "from tarsy.agents.configurable_agent import ConfigurableAgent; from tarsy.models.agent_config import AgentConfigModel; print('ConfigurableAgent and AgentConfigModel can be imported')"
```

**Success Criteria:**
- [ ] ConfigurationLoader handles all file scenarios correctly (missing, malformed, valid)
- [ ] MCP server reference validation works with built-in + configured servers
- [ ] Conflict detection identifies both naming and alert type conflicts
- [ ] ConfigurableAgent properly extends BaseAgent and overrides abstract methods
- [ ] All error scenarios produce clear, actionable error messages
- [ ] All validation commands pass

---

### Phase 3: Integration Layer

**Objective**: Extend existing registries and factory to support configured agents and MCP servers

**Files to Modify:**
- `backend/tarsy/services/agent_registry.py` - Accept and process agent configurations
- `backend/tarsy/services/mcp_server_registry.py` - Accept and merge MCP server configurations  
- `backend/tarsy/services/agent_factory.py` - Create ConfigurableAgent instances

**Key Tasks:**
1. **Extend AgentRegistry**:
   - Add `agent_configs: Optional[Dict[str, AgentConfigModel]] = None` parameter to constructor
   - Implement `_create_configured_mappings()` to convert agent configs to `alert_type -> "ConfigurableAgent:agent-name"` mappings
   - Merge configured mappings with existing static mappings
   - Maintain full backward compatibility with existing usage

2. **Extend MCPServerRegistry**:
   - Add `configured_servers: Optional[Dict[str, MCPServerConfigModel]] = None` parameter to constructor
   - Convert `MCPServerConfigModel` objects to internal format and merge with `_DEFAULT_SERVERS`
   - Maintain existing API compatibility

3. **Extend AgentFactory**:
   - Add `agent_configs: Optional[Dict[str, AgentConfigModel]] = None` parameter to constructor (keeping existing `progress_callback` parameter)
   - Enhance `create_agent()` to handle `"ConfigurableAgent:agent-name"` format
   - Create `ConfigurableAgent` instances with proper dependency injection
   - Maintain full backward compatibility with traditional agent creation

4. **Startup Integration**:
   - Design startup orchestration pattern showing how components are initialized with parsed configuration
   - Ensure centralized configuration loading with distribution to all components

**Validation Steps:**
```bash
# Test agent registry extension
python -c "from tarsy.services.agent_registry import AgentRegistry; registry = AgentRegistry(); print('AgentRegistry backward compatibility maintained')"

# Test MCP server registry extension  
python -c "from tarsy.services.mcp_server_registry import MCPServerRegistry; registry = MCPServerRegistry(); print('MCPServerRegistry backward compatibility maintained')"

# Test agent factory extension (requires mocked dependencies for full instantiation)
python -c "from tarsy.services.agent_factory import AgentFactory; print('AgentFactory can be imported with extended signature')"

# Test end-to-end integration (with mocked dependencies)
python -c "print('Integration validation placeholder - will be implemented in this phase')"
```

**Success Criteria:**
- [ ] AgentRegistry properly converts configured agents to alert type mappings
- [ ] MCPServerRegistry merges configured servers with built-in servers
- [ ] AgentFactory creates both traditional and configurable agents
- [ ] All existing functionality remains unchanged (backward compatibility)
- [ ] Startup orchestration pattern works end-to-end
- [ ] All validation commands pass

---

### Phase 4: Error Handling and Resilience

**Objective**: Implement comprehensive error handling, edge cases, and validation scenarios

**Key Tasks:**
1. **Configuration Error Scenarios**:
   - Invalid YAML syntax with detailed error reporting
   - Missing required fields with field-specific error messages
   - Invalid field values with validation constraint details
   - Circular dependencies in MCP server references

2. **Conflict Detection Enhancement**:
   - Agent name conflicts: configured vs built-in with specific name details
   - MCP server ID conflicts: configured vs built-in with specific ID details  
   - Alert type conflicts: multiple agents handling same alert type with specific conflict details
   - Edge case: empty configuration files, partial configurations

3. **Runtime Error Handling**:
   - ConfigurableAgent runtime errors consistent with BaseAgent error handling
   - Registry lookup failures with clear error messages
   - Factory creation failures with dependency injection error details

4. **Validation Enhancement**:
   - MCP server reference validation across built-in and configured servers
   - Alert type uniqueness validation across all agent sources
   - Configuration file path validation and file system error handling

**Validation Steps:**
```bash
# Test invalid YAML handling
echo "invalid: yaml: [syntax" > test_invalid.yaml
python -c "
from tarsy.config.agent_config import ConfigurationLoader
loader = ConfigurationLoader('test_invalid.yaml')
try: 
    loader.load_and_validate()
    print('ERROR: Should have failed')
except Exception as e: 
    print(f'Invalid YAML handled correctly: {type(e).__name__}')"
rm test_invalid.yaml

# Test conflict detection
python -c "print('Conflict detection tests - will be implemented comprehensively')"

# Test runtime error scenarios
python -c "print('Runtime error scenario tests - will be implemented')"
```

**Success Criteria:**
- [ ] All configuration error scenarios produce clear, actionable error messages
- [ ] Conflict detection covers all specified conflict types with detailed reporting
- [ ] Runtime errors are handled consistently with existing system patterns
- [ ] Edge cases (empty files, missing directories) are handled gracefully
- [ ] Error messages provide sufficient detail for troubleshooting
- [ ] All validation commands pass

---

### Phase 5: Testing and Final Validation

**Objective**: Comprehensive testing, integration validation, and production readiness

**Files to Create:**
- `backend/tests/unit/models/test_agent_config.py` - Pydantic model tests
- `backend/tests/unit/config/test_agent_config.py` - ConfigurationLoader tests
- `backend/tests/unit/agents/test_configurable_agent.py` - ConfigurableAgent tests
- `backend/tests/unit/services/test_agent_registry_extended.py` - AgentRegistry extension tests
- `backend/tests/unit/services/test_mcp_server_registry_extended.py` - MCPServerRegistry extension tests
- `backend/tests/unit/services/test_agent_factory_extended.py` - AgentFactory extension tests
- `backend/tests/integration/test_configurable_agents.py` - End-to-end integration tests

**Key Tasks:**
1. **Unit Testing**:
   - Pydantic model validation with valid and invalid inputs
   - ConfigurationLoader with all file scenarios and error conditions
   - ConfigurableAgent with various configuration inputs
   - AgentRegistry extensions with configured and mixed (built-in + configured) scenarios
   - MCPServerRegistry extensions with configured server merging
   - AgentFactory with traditional and configurable agent creation

2. **Integration Testing**:
   - End-to-end configuration loading → registry population → agent creation flow
   - Mixed usage scenarios: built-in agents + configured agents working together
   - Alert processing with configured agents using both built-in and configured MCP servers
   - Startup integration with actual configuration files

3. **Error Scenario Testing**:
   - All identified error conditions with expected error types and messages
   - Configuration file validation edge cases
   - Conflict detection with various conflict scenarios
   - Runtime error propagation and handling

4. **Documentation and Examples**:
   - Update example configuration with comprehensive documentation
   - Verify all code examples in design document work correctly
   - Ensure configuration template is production-ready

**Validation Steps:**
```bash
# Run comprehensive test suite for all new and modified components
python -m pytest tests/unit/models/test_agent_config.py tests/unit/config/test_agent_config.py tests/unit/agents/test_configurable_agent.py -v
python -m pytest tests/unit/services/test_agent_registry_extended.py tests/unit/services/test_mcp_server_registry_extended.py tests/unit/services/test_agent_factory_extended.py -v

# Run integration tests
python -m pytest tests/integration/test_configurable_agents.py -v

# Test with actual configuration file
cp config/agents.yaml.example config/agents.yaml
AGENT_CONFIG_PATH=./config/agents.yaml python -c "
from tarsy.config.agent_config import ConfigurationLoader
from tarsy.config.settings import get_settings
settings = get_settings()
loader = ConfigurationLoader(settings.agent_config_path)
config = loader.load_and_validate()
print(f'Successfully loaded configuration with {len(config.agents)} agents and {len(config.mcp_servers)} MCP servers')
"

# Test end-to-end with configured agents (integration test)
python -c "print('End-to-end integration test - will verify full workflow')"

# Cleanup test file
rm config/agents.yaml
```

**Success Criteria:**
- [ ] All unit tests pass with comprehensive coverage of business logic
- [ ] Integration tests verify end-to-end functionality  
- [ ] Error scenario tests cover all identified failure modes
- [ ] Configuration examples work correctly in practice
- [ ] All requirements from EP-0006 requirements document are met (REQ-1 through REQ-22, including sub-requirements)
- [ ] All design elements from EP-0006 design document are implemented
- [ ] System maintains full backward compatibility
- [ ] All validation commands pass consistently

---

## Execution Process

### For Each Implementation Phase:

1. **Implement** the functionality for this phase following the specified file changes and key tasks
2. **Test** using the validation commands provided for each phase  
3. **Fix** any issues before proceeding to the next phase
4. **Document** any deviations from the original design or important implementation decisions
5. **Move** to next phase only when current phase passes all validation criteria

### Quality Gates

Before marking any phase complete:
- [ ] All code follows the standards above (docstrings, type hints, error handling, logging)
- [ ] All validation commands pass consistently
- [ ] Tests cover the implemented functionality with appropriate mocking
- [ ] Error handling provides clear, actionable messages
- [ ] Integration points work as expected with existing components
- [ ] Backward compatibility is maintained for all existing functionality

### When Things Go Wrong

- **Test Failures**: Check mocking setup, verify configuration file paths, ensure proper dependency injection
- **Type Errors**: Add missing type annotations, verify Pydantic model imports and usage
- **Import Issues**: Check module structure, verify relative imports, ensure __init__.py files exist
- **Integration Problems**: Verify component initialization order, check dependency injection patterns
- **Configuration Errors**: Validate YAML syntax, check file paths, verify Pydantic model constraints

---

## Definition of Done

An EP-0006 implementation is complete when:
- [ ] All requirements from the requirements document are met (REQ-1 through REQ-22, including sub-requirements REQ-4a, REQ-5a, REQ-16a)
- [ ] All design elements from the design document are implemented  
- [ ] All validation commands pass consistently across all phases
- [ ] Critical functionality has comprehensive test coverage (configuration loading, validation, agent creation, error handling)
- [ ] Code includes proper documentation and structured error handling with ConfigurationError
- [ ] Integration points work as specified: registry population, agent factory creation, startup orchestration
- [ ] Implementation maintains full backward compatibility with existing agent and MCP server functionality
- [ ] System is ready for production use with configuration-based agents alongside hardcoded agents

---

## AI Implementation Notes

### Reading the Design Document
- **Extension Strategy**: This extends existing components rather than replacing them - maintain all existing functionality
- **Component Dependencies**: ConfigurationLoader → Registries → AgentFactory → ConfigurableAgent (follow this order)
- **Compatibility Requirements**: Full backward compatibility required - existing agents must continue working unchanged
- **Integration Pattern**: Centralized configuration loading with distribution to multiple components

### Creating Implementation Plans
- **5 phases chosen** based on complexity: new components + existing extensions + comprehensive validation
- **Logical, testable chunks**: Each phase builds on previous phases and can be independently validated
- **Risk minimization**: Foundation first, integration last, comprehensive testing throughout
- **Early validation enabled**: Each phase has specific validation steps to catch problems quickly

### During Implementation
- **Follow extension patterns**: Use dependency injection, maintain existing APIs, add new optional parameters
- **Comprehensive error handling**: Use ConfigurationError for all configuration-related failures
- **Test thoroughly**: Each phase has specific validation commands - run them after significant changes
- **Document deviations**: Note any changes from the original design and reasons for changes 