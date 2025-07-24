"""
Unit tests for LLM Client - Handles LLM provider integrations via LangChain.

Tests LLM provider communication, message conversion, hook integration,
error handling, availability management, and multi-provider orchestration.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from tarsy.integrations.llm.client import LLMClient, LLMManager, LLM_PROVIDERS
from tarsy.models.llm import LLMMessage
from tarsy.config.settings import Settings


@pytest.mark.unit
class TestLLMClientInitialization:
    """Test LLMClient initialization with different providers and configurations."""
    
    def test_initialization_openai_success(self):
        """Test successful OpenAI client initialization."""
        config = {"model": "gpt-4", "api_key": "sk-test-key", "temperature": 0.5}
        
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_client_instance = Mock()
            mock_openai.return_value = mock_client_instance
            
            client = LLMClient("openai", config)
            
            assert client.provider_name == "openai"
            assert client.model == "gpt-4"
            assert client.api_key == "sk-test-key"
            assert client.temperature == 0.5
            assert client.available is True
            assert client.llm_client == mock_client_instance
    
    def test_initialization_gemini_success(self):
        """Test successful Gemini client initialization."""
        config = {"model": "gemini-pro", "api_key": "gemini-key", "temperature": 0.3}
        
        with patch('tarsy.integrations.llm.client.ChatGoogleGenerativeAI') as mock_gemini:
            mock_client_instance = Mock()
            mock_gemini.return_value = mock_client_instance
            
            client = LLMClient("gemini", config)
            
            assert client.provider_name == "gemini"
            assert client.model == "gemini-pro"
            assert client.available is True
            
            mock_gemini.assert_called_once_with(
                model="gemini-pro",
                temperature=0.3,
                google_api_key="gemini-key"
            )
    
    def test_initialization_grok_success(self):
        """Test successful Grok client initialization."""
        config = {"model": "grok-beta", "api_key": "xai-key", "temperature": 0.7}
        
        with patch('tarsy.integrations.llm.client.ChatXAI') as mock_grok:
            mock_client_instance = Mock()
            mock_grok.return_value = mock_client_instance
            
            client = LLMClient("grok", config)
            
            assert client.provider_name == "grok"
            assert client.available is True
            
            mock_grok.assert_called_once_with(
                model_name="grok-beta",
                api_key="xai-key",
                temperature=0.7
            )
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        config = {"api_key": "test-key"}
        
        with patch('tarsy.integrations.llm.client.ChatOpenAI'):
            client = LLMClient("openai", config)
            
            assert client.model == "default"
            assert client.temperature == 0.3
    
    def test_initialization_without_api_key(self):
        """Test initialization failure when API key is missing."""
        config = {"model": "test-model"}
        
        client = LLMClient("openai", config)
        
        assert client.available is False
        assert client.llm_client is None
        assert client.api_key == ""
    
    def test_initialization_unknown_provider(self):
        """Test initialization failure with unknown provider."""
        config = {"api_key": "test-key", "model": "test-model"}
        
        client = LLMClient("unknown_provider", config)
        
        assert client.available is False
        assert client.llm_client is None
    
    def test_initialization_langchain_error(self):
        """Test initialization failure when LangChain client creation fails."""
        config = {"api_key": "test-key", "model": "test-model"}
        
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_openai.side_effect = Exception("LangChain initialization failed")
            
            client = LLMClient("openai", config)
            
            assert client.available is False
            assert client.llm_client is None


@pytest.mark.unit
class TestLLMClientMessageConversion:
    """Test message conversion from LLMMessage to LangChain messages."""
    
    @pytest.fixture
    def client(self):
        """Create LLMClient instance for testing."""
        config = {"api_key": "test-key", "model": "test-model"}
        with patch('tarsy.integrations.llm.client.ChatOpenAI'):
            return LLMClient("openai", config)
    
    def test_convert_system_message(self, client):
        """Test conversion of system message."""
        messages = [LLMMessage(role="system", content="You are a helpful assistant.")]
        
        result = client._convert_messages(messages)
        
        assert len(result) == 1
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "You are a helpful assistant."
    
    def test_convert_user_message(self, client):
        """Test conversion of user message."""
        messages = [LLMMessage(role="user", content="What is the capital of France?")]
        
        result = client._convert_messages(messages)
        
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
        assert result[0].content == "What is the capital of France?"
    
    def test_convert_assistant_message(self, client):
        """Test conversion of assistant message."""
        messages = [LLMMessage(role="assistant", content="The capital of France is Paris.")]
        
        result = client._convert_messages(messages)
        
        assert len(result) == 1
        assert isinstance(result[0], AIMessage)
        assert result[0].content == "The capital of France is Paris."
    
    def test_convert_multiple_messages(self, client):
        """Test conversion of multiple messages with different roles."""
        messages = [
            LLMMessage(role="system", content="System prompt"),
            LLMMessage(role="user", content="User question"),
            LLMMessage(role="assistant", content="Assistant response")
        ]
        
        result = client._convert_messages(messages)
        
        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert isinstance(result[2], AIMessage)
    
    def test_convert_empty_message_list(self, client):
        """Test conversion of empty message list."""
        result = client._convert_messages([])
        assert result == []
    
    def test_convert_message_with_special_characters(self, client):
        """Test conversion of messages with special characters."""
        messages = [LLMMessage(role="user", content="Emojis 🤖 and unicode: café")]
        
        result = client._convert_messages(messages)
        
        assert result[0].content == "Emojis 🤖 and unicode: café"


@pytest.mark.unit 
class TestLLMClientGenerateResponse:
    """Test the core generate_response method."""
    
    @pytest.fixture
    def client(self):
        """Create LLMClient instance with mocked LangChain client."""
        config = {"api_key": "test-key", "model": "test-model"}
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_langchain_client = AsyncMock()
            mock_openai.return_value = mock_langchain_client
            
            client = LLMClient("openai", config)
            return client
    
    async def test_generate_response_success(self, client):
        """Test successful response generation."""
        mock_response = Mock()
        mock_response.content = "Test response"
        client.llm_client.ainvoke.return_value = mock_response
        
        with patch('tarsy.integrations.llm.client.HookContext') as mock_hook_context:
            mock_context = AsyncMock()
            mock_context.get_request_id.return_value = "req-123"
            mock_hook_context.return_value.__aenter__.return_value = mock_context
            
            messages = [LLMMessage(role="user", content="Test question")]
            result = await client.generate_response(messages)
            
            assert result == "Test response"
            client.llm_client.ainvoke.assert_called_once()
            mock_context.complete_success.assert_called_once()
    
    async def test_generate_response_client_unavailable(self):
        """Test response generation when client is unavailable."""
        config = {"api_key": "test-key"}
        client = LLMClient("openai", config)
        client.available = False
        
        messages = [LLMMessage(role="user", content="Test")]
        
        with pytest.raises(Exception, match="openai client not available"):
            await client.generate_response(messages)
    
    async def test_generate_response_langchain_error(self, client):
        """Test response generation when LangChain call fails."""
        client.llm_client.ainvoke.side_effect = Exception("API rate limit exceeded")
        
        with patch('tarsy.integrations.llm.client.HookContext') as mock_hook_context:
            mock_context = AsyncMock()
            mock_context.get_request_id.return_value = "req-456"
            mock_hook_context.return_value.__aenter__.return_value = mock_context
            
            messages = [LLMMessage(role="user", content="Test")]
            
            with pytest.raises(Exception, match="openai API error"):
                await client.generate_response(messages)


@pytest.mark.unit
class TestLLMClientLogging:
    """Test LLM client logging functionality."""
    
    @pytest.fixture
    def client(self):
        """Create LLMClient instance for testing."""
        config = {"api_key": "test-key", "model": "test-model"}
        with patch('tarsy.integrations.llm.client.ChatOpenAI'):
            return LLMClient("openai", config)
    
    def test_log_llm_request(self, client):
        """Test LLM request logging."""
        messages = [LLMMessage(role="user", content="Test message")]
        
        with patch('tarsy.integrations.llm.client.llm_comm_logger') as mock_logger:
            client._log_llm_request(messages, "req-123", max_tokens=100)
            
            assert mock_logger.info.call_count >= 5
            
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("=== LLM REQUEST [openai] [ID: req-123] ===" in call for call in log_calls)
            assert any("Provider: openai" in call for call in log_calls)
    
    def test_log_llm_response(self, client):
        """Test LLM response logging."""
        response_content = "Test response content"
        
        with patch('tarsy.integrations.llm.client.llm_comm_logger') as mock_logger:
            client._log_llm_response(response_content, "req-456")
            
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("=== LLM RESPONSE [openai] [ID: req-456] ===" in call for call in log_calls)
            assert any(response_content in call for call in log_calls)
    
    def test_log_llm_error(self, client):
        """Test LLM error logging."""
        error_message = "API error occurred"
        
        with patch('tarsy.integrations.llm.client.llm_comm_logger') as mock_logger:
            client._log_llm_error(error_message, "req-error")
            
            log_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("=== LLM ERROR [openai] [ID: req-error] ===" in call for call in log_calls)
            assert any(error_message in call for call in log_calls)


@pytest.mark.unit
class TestLLMManagerInitialization:
    """Test LLMManager initialization and client management."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {
            "openai": {"api_key": "sk-openai-key", "model": "gpt-4"},
            "gemini": {"api_key": "gemini-key", "model": "gemini-pro"}
        }
        settings.default_llm_provider = "openai"
        settings.get_llm_config = lambda x: settings.llm_providers.get(x, {})
        return settings
    
    def test_initialization_multiple_providers(self, mock_settings):
        """Test initialization with multiple LLM providers."""
        with patch('tarsy.integrations.llm.client.LLMClient') as mock_llm_client:
            mock_instance = Mock()
            mock_instance.available = True
            mock_llm_client.return_value = mock_instance
            
            manager = LLMManager(mock_settings)
            
            assert len(manager.clients) == 2
            assert "openai" in manager.clients
            assert "gemini" in manager.clients
            assert mock_llm_client.call_count == 2
    
    def test_initialization_skip_providers_without_api_keys(self):
        """Test that providers without API keys are skipped."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {
            "openai": {"api_key": "sk-openai-key", "model": "gpt-4"},
            "gemini": {"model": "gemini-pro"}  # No API key
        }
        settings.get_llm_config = lambda x: settings.llm_providers.get(x, {})
        
        with patch('tarsy.integrations.llm.client.LLMClient') as mock_llm_client:
            mock_instance = Mock()
            mock_instance.available = True
            mock_llm_client.return_value = mock_instance
            
            manager = LLMManager(settings)
            
            assert len(manager.clients) == 1
            assert "openai" in manager.clients
            assert "gemini" not in manager.clients
    
    def test_initialization_handle_client_creation_errors(self, mock_settings):
        """Test handling of client creation errors."""
        with patch('tarsy.integrations.llm.client.LLMClient') as mock_llm_client:
            def side_effect(provider, config):
                if provider == "gemini":
                    raise Exception("Gemini initialization failed")
                mock_client = Mock()
                mock_client.available = True
                return mock_client
            
            mock_llm_client.side_effect = side_effect
            
            manager = LLMManager(mock_settings)
            
            assert len(manager.clients) == 1
            assert "openai" in manager.clients
            assert "gemini" not in manager.clients
    
    def test_initialization_no_providers(self):
        """Test initialization with no configured providers."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {}
        settings.get_llm_config = lambda x: {}
        
        manager = LLMManager(settings)
        
        assert len(manager.clients) == 0


@pytest.mark.unit
class TestLLMManagerClientManagement:
    """Test LLMManager client retrieval and management."""
    
    @pytest.fixture
    def manager_with_clients(self):
        """Create LLMManager with mock clients."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {"openai": {"api_key": "key1"}, "gemini": {"api_key": "key2"}}
        settings.default_llm_provider = "openai"
        settings.get_llm_config = lambda x: settings.llm_providers.get(x, {})
        
        with patch('tarsy.integrations.llm.client.LLMClient') as mock_llm_client:
            mock_openai = Mock()
            mock_openai.available = True
            mock_gemini = Mock()
            mock_gemini.available = True
            
            mock_llm_client.side_effect = [mock_openai, mock_gemini]
            
            manager = LLMManager(settings)
            return manager
    
    def test_get_client_by_provider(self, manager_with_clients):
        """Test getting client by specific provider name."""
        client = manager_with_clients.get_client("openai")
        assert client is not None
        
        client = manager_with_clients.get_client("gemini")
        assert client is not None
        
        client = manager_with_clients.get_client("nonexistent")
        assert client is None
    
    def test_get_client_default_provider(self, manager_with_clients):
        """Test getting client using default provider."""
        client = manager_with_clients.get_client()
        assert client is not None
        assert client == manager_with_clients.clients["openai"]
    
    def test_list_available_providers(self, manager_with_clients):
        """Test listing available providers."""
        providers = manager_with_clients.list_available_providers()
        assert isinstance(providers, list)
        assert set(providers) == {"openai", "gemini"}
    
    def test_is_available_true(self, manager_with_clients):
        """Test availability check when clients are available."""
        assert manager_with_clients.is_available() is True
    
    def test_is_available_false_no_clients(self):
        """Test availability check when no clients exist."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {}
        settings.get_llm_config = lambda x: {}
        
        manager = LLMManager(settings)
        assert manager.is_available() is False
    
    def test_get_availability_status(self, manager_with_clients):
        """Test getting detailed availability status."""
        status = manager_with_clients.get_availability_status()
        
        assert isinstance(status, dict)
        assert "openai" in status
        assert "gemini" in status
        assert status["openai"] is True
        assert status["gemini"] is True


@pytest.mark.unit
class TestLLMManagerResponseGeneration:
    """Test LLMManager response generation and delegation."""
    
    @pytest.fixture
    def manager_with_mock_client(self):
        """Create LLMManager with mock client."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {"openai": {"api_key": "test-key"}}
        settings.default_llm_provider = "openai"
        settings.get_llm_config = lambda x: settings.llm_providers.get(x, {})
        
        with patch('tarsy.integrations.llm.client.LLMClient') as mock_llm_client:
            mock_client = AsyncMock()
            mock_client.available = True
            mock_client.generate_response.return_value = "Test response"
            mock_llm_client.return_value = mock_client
            
            manager = LLMManager(settings)
            return manager
    
    async def test_generate_response_default_provider(self, manager_with_mock_client):
        """Test response generation with default provider."""
        messages = [LLMMessage(role="user", content="Test message")]
        
        result = await manager_with_mock_client.generate_response(messages)
        
        assert result == "Test response"
        
        openai_client = manager_with_mock_client.clients["openai"]
        openai_client.generate_response.assert_called_once_with(messages)
    
    async def test_generate_response_with_kwargs(self, manager_with_mock_client):
        """Test response generation with additional kwargs."""
        messages = [LLMMessage(role="user", content="Test message")]
        
        await manager_with_mock_client.generate_response(
            messages, 
            max_tokens=100,
            temperature=0.5
        )
        
        openai_client = manager_with_mock_client.clients["openai"]
        openai_client.generate_response.assert_called_once_with(
            messages, 
            max_tokens=100,
            temperature=0.5
        )
    
    async def test_generate_response_provider_not_available(self):
        """Test response generation when requested provider is not available."""
        settings = Mock(spec=Settings)
        settings.llm_providers = {"openai": {"api_key": "key"}}
        settings.get_llm_config = lambda x: settings.llm_providers.get(x, {})
        
        with patch('tarsy.integrations.llm.client.LLMClient'):
            manager = LLMManager(settings)
            messages = [LLMMessage(role="user", content="Test")]
            
            with pytest.raises(Exception, match="LLM provider not available"):
                await manager.generate_response(messages, provider="nonexistent")


@pytest.mark.unit
class TestLLMProvidersConfiguration:
    """Test LLM providers configuration and mapping."""
    
    def test_llm_providers_mapping_structure(self):
        """Test that LLM_PROVIDERS mapping is properly structured."""
        assert isinstance(LLM_PROVIDERS, dict)
        assert "openai" in LLM_PROVIDERS
        assert "gemini" in LLM_PROVIDERS
        assert "grok" in LLM_PROVIDERS
        
        for provider_name, provider_func in LLM_PROVIDERS.items():
            assert callable(provider_func)
    
    def test_openai_provider_creation(self):
        """Test OpenAI provider creation through mapping."""
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            provider_func = LLM_PROVIDERS["openai"]
            result = provider_func(0.5, "test-key", "gpt-4")
            
            mock_openai.assert_called_once_with(
                model_name="gpt-4",
                temperature=0.5,
                api_key="test-key"
            )
            assert result == mock_client
    
    def test_gemini_provider_creation(self):
        """Test Gemini provider creation through mapping."""
        with patch('tarsy.integrations.llm.client.ChatGoogleGenerativeAI') as mock_gemini:
            mock_client = Mock()
            mock_gemini.return_value = mock_client
            
            provider_func = LLM_PROVIDERS["gemini"]
            result = provider_func(0.3, "gemini-key", "gemini-pro")
            
            mock_gemini.assert_called_once_with(
                model="gemini-pro",
                temperature=0.3,
                google_api_key="gemini-key"
            )
            assert result == mock_client
    
    def test_grok_provider_creation(self):
        """Test Grok provider creation through mapping."""
        with patch('tarsy.integrations.llm.client.ChatXAI') as mock_grok:
            mock_client = Mock()
            mock_grok.return_value = mock_client
            
            provider_func = LLM_PROVIDERS["grok"]
            result = provider_func(0.7, "xai-key", "grok-beta")
            
            mock_grok.assert_called_once_with(
                model_name="grok-beta",
                api_key="xai-key",
                temperature=0.7
            )
            assert result == mock_client


@pytest.mark.unit
class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in LLM client components."""
    
    def test_llm_client_with_none_config(self):
        """Test LLMClient behavior with None configuration values."""
        config = {"api_key": None, "model": None, "temperature": None}
        
        client = LLMClient("openai", config)
        
        assert client.api_key is None
        assert client.model is None  # config.get() returns None when value is None
        assert client.temperature is None  # config.get() returns None when value is None
        assert client.available is False
    
    async def test_generate_response_empty_messages(self):
        """Test generate_response with empty message list."""
        config = {"api_key": "test-key"}
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_langchain_client = AsyncMock()
            mock_openai.return_value = mock_langchain_client
            
            client = LLMClient("openai", config)
            
            mock_response = Mock()
            mock_response.content = "Empty response"
            mock_langchain_client.ainvoke.return_value = mock_response
            
            with patch('tarsy.integrations.llm.client.HookContext') as mock_hook_context:
                mock_context = AsyncMock()
                mock_context.get_request_id.return_value = "empty-req"
                mock_hook_context.return_value.__aenter__.return_value = mock_context
                
                result = await client.generate_response([])
                
                assert result == "Empty response"
                mock_langchain_client.ainvoke.assert_called_once_with([])
    
    def test_llm_manager_settings_none(self):
        """Test LLMManager with None settings."""
        with pytest.raises(AttributeError):
            LLMManager(None)
    
    async def test_concurrent_response_generation(self):
        """Test concurrent response generation."""
        import asyncio
        
        config = {"api_key": "test-key"}
        with patch('tarsy.integrations.llm.client.ChatOpenAI') as mock_openai:
            mock_langchain_client = AsyncMock()
            mock_openai.return_value = mock_langchain_client
            
            client = LLMClient("openai", config)
            
            mock_responses = [Mock(content=f"Response {i}") for i in range(3)]
            mock_langchain_client.ainvoke.side_effect = mock_responses
            
            with patch('tarsy.integrations.llm.client.HookContext') as mock_hook_context:
                mock_context = AsyncMock()
                mock_context.get_request_id.side_effect = [f"req-{i}" for i in range(3)]
                mock_hook_context.return_value.__aenter__.return_value = mock_context
                
                messages = [LLMMessage(role="user", content=f"Message {i}") for i in range(3)]
                tasks = [client.generate_response([msg]) for msg in messages]
                results = await asyncio.gather(*tasks)
                
                assert len(results) == 3
                assert results[0] == "Response 0"
                assert results[1] == "Response 1"
                assert results[2] == "Response 2"
                
                assert mock_langchain_client.ainvoke.call_count == 3 