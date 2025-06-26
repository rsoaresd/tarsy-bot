"""
Test script for validating MCP and LLM integration.
"""

import asyncio
import json
from app.config.settings import Settings
from app.integrations.mcp.mcp_client import MCPClient
from app.integrations.llm.client import LLMManager
from app.models.alert import Alert


async def test_mcp_integration():
    """Test the MCP integration with official MCP SDK."""
    print("Testing MCP Integration...")
    
    settings = Settings()
    mcp_client = MCPClient(settings)
    
    try:
        # Initialize MCP servers
        await mcp_client.initialize()
        print("✓ MCP servers initialized")
        
        # List available tools
        tools = await mcp_client.list_tools()
        print(f"✓ Found {sum(len(t) for t in tools.values())} tools across {len(tools)} servers")
        
        # Print some tool names
        for server, server_tools in tools.items():
            print(f"\n{server} server tools ({len(server_tools)}):")
            for tool in server_tools[:5]:  # Show first 5 tools
                print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')[:60]}...")
            if len(server_tools) > 5:
                print(f"  ... and {len(server_tools) - 5} more tools")
                
    except Exception as e:
        print(f"✗ MCP integration test failed: {str(e)}")
        return False
    
    finally:
        await mcp_client.close()
    
    return True


async def test_llm_tool_selection():
    """Test LLM's ability to select MCP tools."""
    print("\n\nTesting LLM Tool Selection...")
    
    settings = Settings()
    mcp_client = MCPClient(settings)
    llm_manager = LLMManager(settings)
    
    try:
        # Initialize MCP servers
        await mcp_client.initialize()
        
        # Get available tools
        available_tools = await mcp_client.list_tools()
        
        # Create a test alert
        test_alert = Alert(
            alert="Namespace is stuck in Terminating",
            severity="high",
            environment="production",
            cluster="test-cluster",
            namespace="stuck-namespace",
            message="Namespace has been terminating for 2 hours",
            runbook="https://github.com/example/runbooks/namespace-stuck.md"
        )
        
        # Test runbook data
        runbook_data = {
            "raw_content": """
# Namespace Stuck in Terminating

## Problem
A namespace is stuck in the Terminating state.

## Investigation Steps
1. Check the namespace status and finalizers
2. List all resources in the namespace
3. Check for any pods that are not terminating
4. Look for events that might explain the issue

## Resolution
1. Remove finalizers if safe to do so
2. Force delete stuck resources
3. Patch the namespace to remove finalizers
"""
}
        
        # Get LLM to determine tools
        llm_client = llm_manager.get_client()
        if not llm_client:
            print("✗ No LLM client available")
            return False
            
        alert_data = test_alert.model_dump()
        tools_to_call = await llm_client.determine_mcp_tools(
            alert_data, runbook_data, available_tools
        )
        
        print(f"✓ LLM selected {len(tools_to_call)} tools to call")
        print("\nSelected tools:")
        for tool in tools_to_call:
            print(f"  - {tool['server']}.{tool['tool']}: {tool['reason']}")
            
    except Exception as e:
        print(f"✗ LLM tool selection test failed: {str(e)}")
        return False
    
    finally:
        await mcp_client.close()
    
    return True


async def main():
    """Run all tests."""
    print("=== MCP and LLM Integration Tests ===\n")
    
    # Test MCP integration
    mcp_success = await test_mcp_integration()
    
    # Test LLM tool selection
    llm_success = await test_llm_tool_selection()
    
    print("\n=== Test Summary ===")
    print(f"MCP Integration: {'✓ PASSED' if mcp_success else '✗ FAILED'}")
    print(f"LLM Tool Selection: {'✓ PASSED' if llm_success else '✗ FAILED'}")
    
    if mcp_success and llm_success:
        print("\n✅ All tests passed! The integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main()) 