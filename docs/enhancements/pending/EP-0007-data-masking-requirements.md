# EP-0007: Data Masking Service for Sensitive MCP Server Data - Requirements Document

**Status:** Draft  
**Created:** 2025-07-31  

---

## Problem Statement

**Current Issue:** MCP servers (Kubernetes, future servers) return sensitive data (secrets, API keys, credentials) that flows unmasked to LLMs, logs, and persistent storage, creating security vulnerabilities.

**Impact:** Sensitive credentials are exposed in LLM prompts, system logs, and history database, violating security best practices and potentially exposing secrets to unauthorized access.

## Solution Requirements

### Functional Requirements

**Core Functionality:**
- [ ] **REQ-1**: Implement pattern-based one-way masking service for secrets and credentials
- [ ] **REQ-2**: Apply masking universally to all MCP server responses before LLM processing, logging, or storage
- [ ] **REQ-3**: Support configurable masking patterns per MCP server through YAML configuration
- [ ] **REQ-3.1**: Provide built-in patterns for common secrets (kubernetes_secret, api_key, password, certificate, token)
- [ ] **REQ-3.2**: Provide built-in pattern groups for common use cases (basic, secrets, security, kubernetes, all)
- [ ] **REQ-3.3**: Support custom regex patterns defined per MCP server in configuration

**User Interface Requirements:**
- [ ] **REQ-4**: No UI changes required - masking is transparent to users
- [ ] **REQ-5**: Maintain existing alert processing workflow without user-visible changes

**Integration Requirements:**
- [ ] **REQ-6**: Integrate masking at single chokepoint in MCPClient.call_tool() method
- [ ] **REQ-7**: Support MCP server-specific masking configuration in existing server configs
- [ ] **REQ-7.1**: Load masking configuration from agents.yaml for configured MCP servers
- [ ] **REQ-7.2**: Support masking configuration in built-in MCP server definitions
- [ ] **REQ-7.3**: Support pattern groups in both built-in and configured MCP servers
- [ ] **REQ-7.4**: Allow mixing of pattern groups and individual patterns per MCP server

### Non-Functional Requirements

**Performance Requirements:**
- [ ] **REQ-8**: Masking processing should add reasonable performance overhead to MCP tool calls
- [ ] **REQ-9**: No additional storage overhead (one-way masking only)

**Security Requirements:**
- [ ] **REQ-10**: Mask all detected secrets/credentials before any logging or LLM processing
- [ ] **REQ-11**: Fail-safe behavior - better to over-mask than under-mask sensitive data

**Reliability Requirements:**
- [ ] **REQ-12**: Masking failures should not break MCP tool execution
- [ ] **REQ-13**: Service should gracefully handle malformed or unexpected data formats
- [ ] **REQ-14**: Basic configuration validation with simple error messaging for invalid patterns

## Success Criteria

### Primary Success Criteria
- [ ] Kubernetes secrets, API keys, and passwords are consistently masked in all system outputs
- [ ] LLM prompts contain no detectable sensitive credentials from MCP servers
- [ ] System logs and history database show masked values instead of raw secrets

### Secondary Success Criteria  
- [ ] Easy addition of new masking patterns through configuration
- [ ] No degradation in alert processing performance
- [ ] Existing MCP server functionality remains unchanged

## Constraints and Limitations

### Technical Constraints
- One-way masking only - no ability to retrieve original values
- Pattern-based detection may have false positives/negatives
- Limited to text-based credential formats in JSON/string responses

### Compatibility Requirements
- Must work with existing MCP client architecture
- Compatible with current logging and history storage systems
- No changes to MCP server implementations required

### Dependencies
- **Internal**: Agent configuration system for loading MCP server masking configs
- **External**: MCP SDK for response format compatibility

## Out of Scope

- PII masking (emails, names, IP addresses) - future enhancement
- Reversible tokenization or credential recovery mechanisms  
- MCP server-side filtering or masking
- UI for managing masking patterns or viewing masked data

---

## Acceptance Criteria

### Functional Acceptance
- [ ] Kubernetes secret data blocks are fully masked in all system components
- [ ] API keys and passwords are detected and masked regardless of JSON structure
- [ ] New MCP servers can be configured with custom masking patterns via YAML
- [ ] Built-in patterns (kubernetes_secret, api_key, password, certificate, token) work across all MCP servers
- [ ] Built-in pattern groups (basic, secrets, security, kubernetes, all) expand to correct individual patterns
- [ ] Custom regex patterns defined in YAML configuration are correctly applied
- [ ] Pattern groups and individual patterns can be mixed in MCP server configuration

### Security Acceptance
- [ ] LLM prompts contain no detectable secrets from MCP server responses
- [ ] Masking service handles edge cases without exposing partial credentials

---

## AI Notes

### Key Information for Design Phase
- **Primary Focus**: Single-point interception in MCPClient with universal pattern-based masking
- **Architecture Impact**: Minimal - add service layer without changing existing data flow
- **Integration Complexity**: Low - single integration point with configurable patterns
- **Performance Criticality**: Medium - must not significantly impact alert processing speed

When creating the design document, ensure all requirements above are addressed with specific technical solutions.