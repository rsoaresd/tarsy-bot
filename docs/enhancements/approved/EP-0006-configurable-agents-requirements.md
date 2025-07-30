# EP-0006: Configuration-Based Agents - Requirements Document

**Status:** Approved  
**Created:** 2025-07-29  

---

## Problem Statement

**Current Issue:** The current agent system requires creating new Python classes that extend BaseAgent and manually updating code (AgentRegistry mappings and AgentFactory imports) to add new agents or MCP servers. While this approach works well for built-in agents, it creates a deployment barrier for production environments where custom agents and MCP servers need to be added without modifying the core codebase, particularly for security-sensitive or closed-source extensions.

**Impact:** 
- Security risk: Cannot deploy closed-source agents without exposing source code
- Operational complexity: Requires code changes and redeployment for new agents
- Limited flexibility: Cannot dynamically configure agents for different environments
- Maintenance burden: Each new agent requires code changes in multiple files

## Solution Requirements

### Functional Requirements

**Core Functionality:**
- [ ] **REQ-1**: System shall support loading agent configurations from filesystem-based YAML file outside the core codebase, without requiring Python code changes
- [ ] **REQ-2**: System shall support loading MCP server configurations from the same YAML file as agent configurations  
- [ ] **REQ-3**: ConfigurableAgent class shall extend BaseAgent and read behavior from configuration instead of hardcoded methods
- [ ] **REQ-4**: Agent configurations shall support defining multiple agents in a single YAML file, each with alert type mappings, MCP server assignments, and custom instructions
- [ ] **REQ-4a**: Each configured agent's alert_types field shall automatically populate the AgentRegistry with mappings from alert type to configured agent name
- [ ] **REQ-5**: MCP server configurations shall include connection parameters and embedded LLM instructions
- [ ] **REQ-5a**: Configured agents shall be able to reference both built-in MCP servers (e.g., "kubernetes-server") and configured MCP servers in their mcp_servers field
- [ ] **REQ-6**: System shall merge built-in agent and MCP server configurations with filesystem-based configuration file deployed alongside the application
- [ ] **REQ-7**: System shall validate all configurations at startup before processing alerts
- [ ] **REQ-8**: System shall detect conflicts between configured and built-in agents/MCP servers (same names/IDs) and fail to start with clear error messages

**User Interface Requirements:**
- [ ] **REQ-9**: Configuration file shall use human-readable YAML format with clear structure
- [ ] **REQ-10**: Configuration validation errors shall provide clear, actionable error messages
- [ ] **REQ-11**: System shall log configuration loading status and any detected conflicts during startup validation

**Integration Requirements:**
- [ ] **REQ-12**: New configuration system shall integrate seamlessly with existing AgentRegistry and MCPServerRegistry
- [ ] **REQ-13**: System shall support BOTH hardcoded agents (extending BaseAgent) AND configuration-based agents simultaneously
- [ ] **REQ-14**: Existing built-in agents (KubernetesAgent) shall continue to work without modification
- [ ] **REQ-15**: AgentFactory shall support creating both traditional BaseAgent subclasses and ConfigurableAgent instances
- [ ] **REQ-16**: Combined agent and MCP server configuration file path shall be configurable via environment variable (AGENT_CONFIG_PATH) with default location `./config/agents.yaml`
- [ ] **REQ-16a**: AGENT_CONFIG_PATH setting shall be added to the application's Settings class and .env template

### Non-Functional Requirements

**Security Requirements:**
- [ ] **REQ-17**: Configuration file shall not allow arbitrary code execution (no Python eval/exec)
- [ ] **REQ-18**: Configuration file access shall be restricted to designated filesystem directories only (no arbitrary file system access)
- [ ] **REQ-19**: MCP server connection parameters shall support secure credential management

**Reliability Requirements:**
- [ ] **REQ-20**: System shall gracefully handle missing configuration file by using only built-in agents and MCP servers
- [ ] **REQ-21**: System shall fail to start with clear error messages if configuration file exists but is malformed or invalid
- [ ] **REQ-22**: Configuration validation errors shall be logged with specific details about what is wrong and how to fix it

## Success Criteria

### Primary Success Criteria
- [ ] Production deployment can add new agents and MCP servers by editing the single configuration file without code changes
- [ ] Multiple agents and MCP servers can be defined and deployed simultaneously in a single YAML configuration file
- [ ] ConfigurableAgent can process alerts using only configuration-defined behavior (custom instructions, MCP servers)

### Secondary Success Criteria  
- [ ] Both hardcoded agents (extending BaseAgent) and configuration-based agents work simultaneously in the same system
- [ ] Developers can still create traditional BaseAgent subclasses exactly as before (KubernetesAgent pattern preserved)
- [ ] Configuration validation catches common mistakes and provides helpful error messages
- [ ] Documentation enables users to create new agent configurations without technical assistance
- [ ] System maintains full backward compatibility with existing agent implementations

## Constraints and Limitations

### Technical Constraints
- Configuration-based agents limited to BaseAgent functionality (no custom Python logic beyond prompts)
- Single YAML file structure must be parseable by standard PyYAML library  
- Must maintain compatibility with existing multi-layer agent architecture
- Configuration file is filesystem-based only (not remote APIs, databases, or network sources)
- Configuration file path must be resolvable relative to application working directory

### Compatibility Requirements
- Must work with existing LLM providers and MCP client architecture
- Must integrate with current AlertService and processing pipeline
- Configuration format should be extensible for future enhancements

### Dependencies
- **Internal**: Depends on existing BaseAgent, AgentRegistry, MCPServerRegistry, AgentFactory, and Settings classes
- **External**: Requires PyYAML library for parsing single configuration file and file system access for configuration loading

## Out of Scope

- Dynamic agent code loading or arbitrary Python execution (reserved for future Plugin System enhancement)
- Hot-reloading of configurations without system restart (configuration changes require restart)
- Configuration management UI or web interface
- Agent versioning or rollback capabilities
- Configuration encryption or advanced security features

---

## Acceptance Criteria

### Functional Acceptance
- [ ] New agent can be deployed by adding entries to the single configuration YAML file
- [ ] New MCP server can be deployed by adding entries to the same configuration YAML file
- [ ] Multiple agents and MCP servers can be defined in a single YAML configuration file
- [ ] Each configured agent processes its assigned alert types correctly and independently
- [ ] Configured agent's alert_types field automatically creates AgentRegistry mappings (e.g., "SecurityBreach" → "ConfigurableAgent:security-agent")
- [ ] Configured agents can reference both built-in MCP servers ("kubernetes-server") and configured MCP servers ("security-server") in their mcp_servers field
- [ ] System can load configuration from custom file path specified in AGENT_CONFIG_PATH environment variable
- [ ] System successfully merges built-in and configured agents/MCP servers when no naming conflicts exist
- [ ] System fails to start with clear error messages when there are naming conflicts between configured and built-in agents/MCP servers (e.g., configured agent named "KubernetesAgent" or MCP server with ID "kubernetes-server")
- [ ] ConfigurableAgent processes alerts identically to equivalent hardcoded agent

### Performance Acceptance
- [ ] Configuration loading does not significantly impact system startup time
- [ ] Agent instantiation time remains comparable to current BaseAgent subclasses

### Security Acceptance
- [ ] Configuration file cannot execute arbitrary code or access unauthorized system resources
- [ ] Malformed configuration file causes system startup failure with clear error messages (no silent failures)
- [ ] MCP server credentials can be configured securely without exposing sensitive data in logs

---

## AI Notes

### Key Information for Design Phase
- **Primary Focus**: Configuration-driven agent behavior replacement for hardcoded Python classes
- **Architecture Impact**: Medium - extends existing registries and factory, adds new ConfigurableAgent class
- **Integration Complexity**: Low - builds on existing BaseAgent architecture with configuration layer
- **Performance Criticality**: Medium - configuration loading happens at startup, agent creation happens per alert

When creating the design document, ensure all requirements above are addressed with specific technical solutions for:
1. Combined configuration file structure and validation for both agents and MCP servers
2. ConfigurableAgent implementation extending BaseAgent
3. Registry modifications to support BOTH hardcoded and configuration-based agents/MCP servers
4. AgentFactory modifications to create both traditional BaseAgent subclasses and ConfigurableAgent instances
5. Alert type to agent mapping automation (REQ-4a) from configured agent alert_types fields
6. Mixed MCP server usage support (REQ-5a) allowing configured agents to use both built-in and configured MCP servers
7. Full backward compatibility preserving the existing KubernetesAgent pattern
8. Conflict detection between configured and built-in agents/MCP servers with fail-fast startup
9. Fail-fast startup behavior for malformed configurations with clear error messages 