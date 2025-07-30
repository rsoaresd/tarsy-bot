"""
Unit tests for AgentRegistry - Maps alert types to agent classes.

Tests alert type to agent class mapping, registry initialization,
lookups, supported types, and edge case handling.
"""


import pytest

from tarsy.services.agent_registry import AgentRegistry


@pytest.mark.unit
class TestAgentRegistryInitialization:
    """Test AgentRegistry initialization with different configurations."""
    
    def test_initialization_with_default_mappings(self):
        """Test initialization using default mappings."""
        registry = AgentRegistry()
        
        # Should have default mappings
        assert isinstance(registry.static_mappings, dict)
        assert len(registry.static_mappings) >= 1
        assert "NamespaceTerminating" in registry.static_mappings
        assert registry.static_mappings["NamespaceTerminating"] == "KubernetesAgent"
    
    def test_initialization_with_custom_config(self):
        """Test initialization with custom configuration."""
        custom_config = {
            "CustomAlert": "CustomAgent",
            "AnotherAlert": "AnotherAgent"
        }
        
        registry = AgentRegistry(config=custom_config)
        
        # Should use custom configuration instead of defaults
        assert registry.static_mappings == custom_config
        assert "CustomAlert" in registry.static_mappings
        assert "AnotherAlert" in registry.static_mappings
        assert "NamespaceTerminating" not in registry.static_mappings
    
    def test_initialization_with_empty_config(self):
        """Test initialization with empty configuration falls back to defaults."""
        registry = AgentRegistry(config={})
        
        # Empty dict is falsy, so should fall back to default mappings
        assert "NamespaceTerminating" in registry.static_mappings
        assert registry.static_mappings["NamespaceTerminating"] == "KubernetesAgent"
        assert len(registry.static_mappings) >= 1
    
    def test_initialization_with_none_config(self):
        """Test initialization with None configuration falls back to defaults."""
        registry = AgentRegistry(config=None)
        
        # Should use default mappings
        assert "NamespaceTerminating" in registry.static_mappings
        assert registry.static_mappings["NamespaceTerminating"] == "KubernetesAgent"
    
    def test_static_mappings_isolation(self):
        """Test that different registry instances have isolated mappings."""
        registry1 = AgentRegistry()
        registry2 = AgentRegistry()
        
        # Should be separate instances
        assert registry1.static_mappings is not registry2.static_mappings
        
        # But should have same content
        assert registry1.static_mappings == registry2.static_mappings
    
    def test_initialization_preserves_config_reference(self):
        """Test that registry uses the provided config directly (implementation behavior)."""
        external_config = {"TestAlert": "TestAgent"}
        registry = AgentRegistry(config=external_config)
        
        # Modify external config
        external_config["NewAlert"] = "NewAgent"
        
        # Registry IS affected because it uses direct reference
        assert "NewAlert" in registry.static_mappings
        assert len(registry.static_mappings) == 2


@pytest.mark.unit
class TestAgentLookup:
    """Test core agent lookup functionality."""
    
    @pytest.fixture
    def sample_registry(self):
        """Create a registry with known mappings for testing."""
        return AgentRegistry(config={
            "NamespaceTerminating": "KubernetesAgent",
            "PodCrash": "KubernetesAgent",
            "HighCPU": "MonitoringAgent",
            "DiskFull": "SystemAgent"
        })
    
    def test_get_agent_for_known_alert_type(self, sample_registry):
        """Test getting agent for known alert types."""
        assert sample_registry.get_agent_for_alert_type("NamespaceTerminating") == "KubernetesAgent"
        assert sample_registry.get_agent_for_alert_type("PodCrash") == "KubernetesAgent"
        assert sample_registry.get_agent_for_alert_type("HighCPU") == "MonitoringAgent"
        assert sample_registry.get_agent_for_alert_type("DiskFull") == "SystemAgent"
    
    def test_get_agent_for_unknown_alert_type(self, sample_registry):
        """Test getting agent for unknown alert types raises ValueError."""
        with pytest.raises(ValueError, match="No agent for alert type 'UnknownAlert'"):
            sample_registry.get_agent_for_alert_type("UnknownAlert")
            
        with pytest.raises(ValueError, match="No agent for alert type 'NonExistentAlert'"):
            sample_registry.get_agent_for_alert_type("NonExistentAlert")
            
        with pytest.raises(ValueError, match="No agent for alert type 'RandomType'"):
            sample_registry.get_agent_for_alert_type("RandomType")
    
    def test_get_agent_case_sensitive(self, sample_registry):
        """Test that agent lookup is case sensitive."""
        # Exact case should work
        assert sample_registry.get_agent_for_alert_type("NamespaceTerminating") == "KubernetesAgent"
        
        # Different case should raise ValueError
        with pytest.raises(ValueError, match="No agent for alert type 'namespaceterminating'"):
            sample_registry.get_agent_for_alert_type("namespaceterminating")
            
        with pytest.raises(ValueError, match="No agent for alert type 'NAMESPACETERMINATING'"):
            sample_registry.get_agent_for_alert_type("NAMESPACETERMINATING")
            
        with pytest.raises(ValueError, match="No agent for alert type 'namespaceTerminating'"):
            sample_registry.get_agent_for_alert_type("namespaceTerminating")
    
    def test_get_agent_with_whitespace_handling(self, sample_registry):
        """Test agent lookup with whitespace."""
        # Whitespace should not match
        with pytest.raises(ValueError, match="No agent for alert type ' NamespaceTerminating'"):
            sample_registry.get_agent_for_alert_type(" NamespaceTerminating")
            
        with pytest.raises(ValueError, match="No agent for alert type 'NamespaceTerminating '"):
            sample_registry.get_agent_for_alert_type("NamespaceTerminating ")
            
        with pytest.raises(ValueError, match="No agent for alert type ' NamespaceTerminating '"):
            sample_registry.get_agent_for_alert_type(" NamespaceTerminating ")
    
    def test_get_agent_with_empty_string(self, sample_registry):
        """Test agent lookup with empty string."""
        with pytest.raises(ValueError, match="No agent for alert type ''"):
            sample_registry.get_agent_for_alert_type("")
    
    def test_get_agent_with_none(self, sample_registry):
        """Test agent lookup with None input."""
        with pytest.raises(ValueError, match="No agent for alert type 'None'"):
            sample_registry.get_agent_for_alert_type(None)
    
    def test_multiple_alert_types_same_agent(self, sample_registry):
        """Test multiple alert types mapping to same agent."""
        # Both should map to KubernetesAgent
        assert sample_registry.get_agent_for_alert_type("NamespaceTerminating") == "KubernetesAgent"
        assert sample_registry.get_agent_for_alert_type("PodCrash") == "KubernetesAgent"
        
        # Should be the same agent class name
        agent1 = sample_registry.get_agent_for_alert_type("NamespaceTerminating")
        agent2 = sample_registry.get_agent_for_alert_type("PodCrash")
        assert agent1 == agent2


@pytest.mark.unit
class TestSupportedAlertTypes:
    """Test supported alert types functionality."""
    
    @pytest.fixture
    def sample_registry(self):
        """Create a registry with known mappings for testing."""
        return AgentRegistry(config={
            "NamespaceTerminating": "KubernetesAgent",
            "PodCrash": "KubernetesAgent", 
            "HighCPU": "MonitoringAgent",
            "DiskFull": "SystemAgent"
        })
    
    def test_get_supported_alert_types_returns_all_keys(self, sample_registry):
        """Test that get_supported_alert_types returns all registered types."""
        supported_types = sample_registry.get_supported_alert_types()
        
        expected_types = ["NamespaceTerminating", "PodCrash", "HighCPU", "DiskFull"]
        assert set(supported_types) == set(expected_types)
        assert len(supported_types) == 4
    
    def test_get_supported_alert_types_returns_list(self, sample_registry):
        """Test that get_supported_alert_types returns a list."""
        supported_types = sample_registry.get_supported_alert_types()
        assert isinstance(supported_types, list)
    
    def test_get_supported_alert_types_truly_empty_registry(self):
        """Test get_supported_alert_types with truly empty registry."""
        # Create registry with defaults first, then clear it
        registry = AgentRegistry()
        registry.static_mappings.clear()  # Make it truly empty
        supported_types = registry.get_supported_alert_types()
        
        assert isinstance(supported_types, list)
        assert len(supported_types) == 0
        assert supported_types == []
    
    def test_get_supported_alert_types_immutable(self, sample_registry):
        """Test that modifying returned list doesn't affect registry."""
        supported_types = sample_registry.get_supported_alert_types()
        original_length = len(supported_types)
        
        # Modify the returned list
        supported_types.append("NewAlertType")
        
        # Registry should not be affected
        new_supported_types = sample_registry.get_supported_alert_types()
        assert len(new_supported_types) == original_length
        assert "NewAlertType" not in new_supported_types
    
    def test_get_supported_alert_types_order_consistency(self, sample_registry):
        """Test that supported types order is consistent."""
        types1 = sample_registry.get_supported_alert_types()
        types2 = sample_registry.get_supported_alert_types()
        
        # Should return same elements (though order may vary)
        assert set(types1) == set(types2)


@pytest.mark.unit
class TestDefaultMappings:
    """Test default mapping configuration."""
    
    def test_default_mappings_contain_kubernetes_agent(self):
        """Test that default mappings include KubernetesAgent."""
        registry = AgentRegistry()
        
        # Should have NamespaceTerminating -> KubernetesAgent
        assert "NamespaceTerminating" in registry.static_mappings
        assert registry.static_mappings["NamespaceTerminating"] == "KubernetesAgent"
    
    def test_default_mappings_structure(self):
        """Test the structure of default mappings."""
        registry = AgentRegistry()
        
        # All keys should be strings
        for alert_type in registry.static_mappings.keys():
            assert isinstance(alert_type, str)
            assert len(alert_type) > 0
        
        # All values should be strings
        for agent_class in registry.static_mappings.values():
            assert isinstance(agent_class, str)
            assert len(agent_class) > 0
    
    def test_default_mappings_not_empty(self):
        """Test that default mappings are not empty."""
        registry = AgentRegistry()
        
        assert len(registry.static_mappings) > 0
        assert registry.static_mappings  # Truthy check
    
    def test_access_to_default_mappings_class_constant(self):
        """Test that _DEFAULT_MAPPINGS class constant exists and is accessible."""
        # Should be able to access the class constant
        assert hasattr(AgentRegistry, '_DEFAULT_MAPPINGS')
        assert isinstance(AgentRegistry._DEFAULT_MAPPINGS, dict)
        assert "NamespaceTerminating" in AgentRegistry._DEFAULT_MAPPINGS


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_registry_with_special_characters_in_alert_type(self):
        """Test registry with special characters in alert types."""
        special_config = {
            "Alert-With-Dashes": "DashAgent",
            "Alert_With_Underscores": "UnderscoreAgent",
            "Alert.With.Dots": "DotAgent",
            "Alert/With/Slashes": "SlashAgent",
            "Alert With Spaces": "SpaceAgent"
        }
        
        registry = AgentRegistry(config=special_config)
        
        # All should be accessible
        assert registry.get_agent_for_alert_type("Alert-With-Dashes") == "DashAgent"
        assert registry.get_agent_for_alert_type("Alert_With_Underscores") == "UnderscoreAgent"
        assert registry.get_agent_for_alert_type("Alert.With.Dots") == "DotAgent"
        assert registry.get_agent_for_alert_type("Alert/With/Slashes") == "SlashAgent"
        assert registry.get_agent_for_alert_type("Alert With Spaces") == "SpaceAgent"
    
    def test_registry_with_numeric_alert_types(self):
        """Test registry with numeric or mixed alert types."""
        numeric_config = {
            "Alert123": "NumericAgent",
            "123Alert": "LeadingNumericAgent",
            "Alert-2024": "YearAgent"
        }
        
        registry = AgentRegistry(config=numeric_config)
        
        assert registry.get_agent_for_alert_type("Alert123") == "NumericAgent"
        assert registry.get_agent_for_alert_type("123Alert") == "LeadingNumericAgent"
        assert registry.get_agent_for_alert_type("Alert-2024") == "YearAgent"
    
    def test_registry_with_unicode_characters(self):
        """Test registry with unicode characters."""
        unicode_config = {
            "AlertWithÜnicode": "UnicodeAgent",
            "Alert🚨Emergency": "EmojiAgent"
        }
        
        registry = AgentRegistry(config=unicode_config)
        
        assert registry.get_agent_for_alert_type("AlertWithÜnicode") == "UnicodeAgent"
        assert registry.get_agent_for_alert_type("Alert🚨Emergency") == "EmojiAgent"
    
    def test_registry_with_very_long_names(self):
        """Test registry with very long alert type and agent names."""
        long_alert_type = "VeryLongAlertTypeName" * 10  # 200+ characters
        long_agent_name = "VeryLongAgentClassName" * 10  # 200+ characters
        
        long_config = {long_alert_type: long_agent_name}
        registry = AgentRegistry(config=long_config)
        
        assert registry.get_agent_for_alert_type(long_alert_type) == long_agent_name
    
    def test_registry_with_empty_string_keys_or_values(self):
        """Test registry behavior with empty string keys or values."""
        empty_config = {
            "": "EmptyKeyAgent",
            "EmptyValueAlert": ""
        }
        
        registry = AgentRegistry(config=empty_config)
        
        # Should handle empty strings
        assert registry.get_agent_for_alert_type("") == "EmptyKeyAgent"
        assert registry.get_agent_for_alert_type("EmptyValueAlert") == ""
    
    def test_get_agent_with_non_string_input(self):
        """Test get_agent_for_alert_type with non-string inputs."""
        registry = AgentRegistry()
        
        # Hashable non-string inputs should raise ValueError
        with pytest.raises(ValueError, match="No agent for alert type '123'"):
            registry.get_agent_for_alert_type(123)
            
        with pytest.raises(ValueError, match="No agent for alert type 'True'"):
            registry.get_agent_for_alert_type(True)
            
        with pytest.raises(ValueError, match="No agent for alert type 'False'"):
            registry.get_agent_for_alert_type(False)
        
        # Unhashable inputs should raise TypeError (implementation behavior)
        with pytest.raises(TypeError):
            registry.get_agent_for_alert_type([])
        
        with pytest.raises(TypeError):
            registry.get_agent_for_alert_type({})


@pytest.mark.unit
class TestRegistryLogging:
    """Test logging functionality in AgentRegistry."""
    
    def test_initialization_logging(self, caplog):
        """Test that initialization logs correct information."""
        with caplog.at_level("INFO"):
            registry = AgentRegistry()
        
        # Should log number of mappings
        log_messages = [record.message for record in caplog.records]
        registry_logs = [msg for msg in log_messages if "Initialized Agent Registry with" in msg]
        assert len(registry_logs) > 0
        
        # Should mention the number of mappings
        registry_log = registry_logs[0]
        assert "mappings" in registry_log
        assert str(len(registry.static_mappings)) in registry_log
    
    def test_initialization_logging_with_custom_config(self, caplog):
        """Test logging with custom configuration."""
        custom_config = {"Alert1": "Agent1", "Alert2": "Agent2"}
        
        with caplog.at_level("INFO"):
            registry = AgentRegistry(config=custom_config)
        
        # Should log correct count
        log_messages = [record.message for record in caplog.records]
        registry_logs = [msg for msg in log_messages if "Initialized Agent Registry with" in msg]
        assert len(registry_logs) > 0
        
        registry_log = registry_logs[0]
        assert "2 total mappings" in registry_log
    
    def test_initialization_logging_with_empty_config(self, caplog):
        """Test logging with empty configuration (falls back to defaults)."""
        with caplog.at_level("INFO"):
            registry = AgentRegistry(config={})
        
        # Should log default mappings count (since empty dict falls back to defaults)
        log_messages = [record.message for record in caplog.records]
        registry_logs = [msg for msg in log_messages if "Initialized Agent Registry with" in msg]
        assert len(registry_logs) > 0
        
        registry_log = registry_logs[0]
        assert str(len(registry.static_mappings)) + " total mappings" in registry_log 