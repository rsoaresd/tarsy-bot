#!/usr/bin/env python3
"""
Test script for LangChain integration.
"""

import asyncio
import os
from dotenv import load_dotenv

from app.config.settings import Settings
from app.integrations.llm.client import LLMManager
from app.models.llm import LLMMessage

# Load environment variables
load_dotenv()


async def test_langchain_integration():
    """Test the LangChain integration."""
    
    print("🧪 Testing LangChain Integration")
    print("=" * 50)
    
    try:
        # Initialize settings
        settings = Settings()
        
        # Initialize LLM Manager
        llm_manager = LLMManager(settings)
        
        # List available providers
        available_providers = llm_manager.list_available_providers()
        print(f"✅ Available LLM providers: {available_providers}")
        
        if not available_providers:
            print("❌ No LLM providers available. Check your API keys.")
            return
        
        # Test each provider (all use unified implementation)
        for provider in available_providers:
            print(f"\n🔍 Testing provider: {provider}")
            
            try:
                client = llm_manager.get_client(provider)
                print(f"  📋 Client type: {type(client).__name__}")
                
                # Create test messages
                messages = [
                    LLMMessage(
                        role="system",
                        content="You are a helpful assistant. Respond concisely."
                    ),
                    LLMMessage(
                        role="user",
                        content="Hello! Please respond with just 'Hello from LangChain!'"
                    )
                ]
                
                # Test generate_response
                response = await client.generate_response(messages)
                print(f"  ✅ Response: {response[:100]}...")
                
                # Test analyze_alert with mock data
                mock_alert = {
                    "alert": "Test Alert",
                    "severity": "High",
                    "cluster": "test-cluster",
                    "namespace": "test-namespace"
                }
                mock_runbook = {
                    "raw_content": "Test runbook",
                }
                mock_mcp_data = {"kubernetes": {"status": "healthy"}}

                analysis = await client.analyze_alert(mock_alert, mock_runbook, mock_mcp_data)
                print(f"  ✅ Analysis: {analysis[:100]}...")
                
            except Exception as e:
                print(f"  ❌ Error testing {provider}: {str(e)}")
        
        print(f"\n🎉 LangChain integration test completed!")
        print(f"📊 Architecture: All providers use UnifiedLLMClient")
        print(f"🔧 Simplified: No provider-specific files needed")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_langchain_integration()) 