# LangChain Integration Migration

## Overview

The SRE AI Agent has been migrated from direct API clients to **LangChain** for improved standardization, reliability, and maintainability. This migration provides:

- ✅ Unified interface across all LLM providers
- ✅ Better error handling and retry logic
- ✅ Standardized message formatting
- ✅ Improved extensibility for future LLM providers
- ✅ Built-in streaming and async support

## Changes Made

### 1. Updated Dependencies

**New dependencies added to `requirements.txt`:**
```
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langchain-google-genai>=2.0.0
langchain-xai>=0.1.0
```

**Removed dependencies:**
```
google-generativeai>=0.3.0  # Now handled by langchain-google-genai
openai>=1.6.0              # Now handled by langchain-openai
```

### 2. New Models

**Created `app/models/llm.py`:**
- `LLMMessage`: Standardized message format for conversations
- `AvailableLLMs`: Enum of supported LLM providers
- `LLMRequest`: Request structure for LLM calls
- `LLMResponse`: Response structure from LLM calls

### 3. Refactored LLM Integration

**Updated `app/integrations/llm/base.py`:**
- `LLM_PROVIDERS`: Dictionary mapping provider names to LangChain clients
- `BaseLLMClient`: Base class now uses LangChain's `BaseChatModel`
- `LLMManager`: Maintains the same interface but uses LangChain internally

**Simplified to unified implementation:**
- `client.py`: Single `UnifiedLLMClient` that works with all providers via LangChain
- **Removed**: `openai.py`, `gemini.py`, `grok.py` (no longer needed)
- All providers now use the same implementation through LangChain abstraction

## Simplified Architecture

### Before: Multiple Provider Files
```
app/integrations/llm/
├── base.py           # Base classes and manager
├── openai.py         # OpenAI-specific implementation
├── gemini.py         # Gemini-specific implementation
└── grok.py           # Grok-specific implementation
```

### After: Unified Implementation
```
app/integrations/llm/
├── base.py           # Base classes, manager, and LLM_PROVIDERS
└── client.py         # Single UnifiedLLMClient for all providers
```

**Key Benefits:**
- ✅ **Reduced Code Duplication**: Single implementation for all providers
- ✅ **Easier Maintenance**: Changes apply to all providers automatically
- ✅ **Consistent Behavior**: All providers have identical functionality
- ✅ **Simplified Testing**: One client type to test instead of three

## LLM Provider Configuration

### Current Supported Providers

```python
LLM_PROVIDERS = {
    "ChatGPT 4.1": lambda temp: ChatOpenAI(
        model_name="gpt-4-1106-preview", 
        temperature=temp, 
        api_key=os.getenv("OPENAI_API_KEY")
    ),
    "Gemini 2.5 Pro": lambda temp: ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-exp-03-25", 
        temperature=temp, 
        google_api_key=os.getenv("GOOGLE_API_KEY")
    ),
    "Grok 3": lambda temp: ChatXAI(
        model_name="grok-3-latest", 
        api_key=os.getenv("GROK_API_KEY"), 
        temperature=temp
    ),
}
```

### Environment Variables Required

```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Grok (X.AI)
GROK_API_KEY=your_grok_api_key
```

## Usage Examples

### Basic Message Creation

```python
from app.models.llm import LLMMessage

# Create messages for conversation
messages = [
    LLMMessage(
        role="system",
        content="You are an expert SRE analyzing system alerts."
    ),
    LLMMessage(
        role="user", 
        content="Analyze this Kubernetes namespace issue..."
    )
]
```

### Using LLM Manager

```python
from app.integrations.llm.client import LLMManager
from app.config.settings import Settings

# Initialize
settings = Settings()
llm_manager = LLMManager(settings)

# List available providers
providers = llm_manager.list_available_providers()
print(f"Available: {providers}")

# Get specific client
client = llm_manager.get_client("ChatGPT 4.1")

# Generate response
response = await client.generate_response(messages)
```

### Alert Analysis

```python
# Analyze alert (existing interface unchanged)
analysis = await llm_manager.analyze_alert(
    alert_data=alert.model_dump(),
    runbook_data=runbook_data,
    mcp_data=mcp_data,
    provider="Gemini 2.5 Pro"  # Optional, uses default if not specified
)
```

## Testing the Integration

Run the test script to verify LangChain integration:

```bash
cd backend
python test_langchain_integration.py
```

Expected output:
```
🧪 Testing LangChain Integration
==================================================
✅ Available LLM providers: ['ChatGPT 4.1', 'Gemini 2.5 Pro', 'Grok 3']

🔍 Testing provider: ChatGPT 4.1
  ✅ Response: Hello from LangChain!...
  ✅ Analysis: Based on the alert data provided...

🎉 LangChain integration test completed!
```

## Migration Impact

### ✅ No Breaking Changes
- All existing API endpoints continue to work
- Alert processing workflow remains unchanged
- WebSocket updates continue to function
- Frontend requires no modifications

### ✅ Improved Reliability
- Better error handling and retries
- Standardized timeout handling
- Improved connection management
- More robust API interactions

### ✅ Future Extensibility
- Easy to add new LLM providers
- Support for streaming responses
- Built-in conversation memory
- Tool calling capabilities

## Adding New LLM Providers

Adding a new LLM provider is now extremely simple:

1. **Install LangChain integration:**
   ```bash
   pip install langchain-[provider]
   ```

2. **Add to LLM_PROVIDERS dictionary in `base.py`:**
   ```python
   LLM_PROVIDERS = {
       # ... existing providers ...
       "New Provider": lambda temp: NewProviderChat(
           model="model-name",
           temperature=temp,
           api_key=os.getenv("NEW_PROVIDER_API_KEY")
       ),
   }
   ```

3. **Update settings configuration:**
   ```bash
   # Add to your .env
   NEW_PROVIDER_API_KEY=your_api_key
   ```

**That's it!** No need to create separate client files - the `UnifiedLLMClient` automatically works with any LangChain-compatible provider.

## Troubleshooting

### Common Issues

1. **Import errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **API key issues:**
   - Ensure all required API keys are set in `.env`
   - Check API key permissions and quotas

3. **Model availability:**
   - Some models may require special access
   - Check provider documentation for model names

4. **Connection issues:**
   - LangChain has built-in retry logic
   - Check network connectivity and API status

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("langchain").setLevel(logging.DEBUG)
```

## Performance Considerations

- **Async Support**: All LangChain clients support async operations
- **Connection Pooling**: Automatic connection management
- **Rate Limiting**: Built-in respect for API rate limits
- **Caching**: Optional response caching available

## Security Notes

- API keys are handled securely through environment variables
- No API keys stored in code or logs
- LangChain provides additional security features like request/response filtering 