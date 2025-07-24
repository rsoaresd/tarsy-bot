"""
Unit tests for RunbookService - Handles runbook downloads from GitHub.

Tests HTTP operations for GitHub runbook downloads, URL conversion,
authentication handling, error scenarios, and resource cleanup.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from tarsy.config.settings import Settings
from tarsy.services.runbook_service import RunbookService


@pytest.mark.unit
class TestRunbookServiceInitialization:
    """Test RunbookService initialization and configuration."""
    
    @pytest.fixture
    def mock_settings_no_token(self):
        """Create mock settings without GitHub token."""
        settings = Mock(spec=Settings)
        settings.github_token = None
        return settings
    
    @pytest.fixture
    def mock_settings_with_token(self):
        """Create mock settings with GitHub token."""
        settings = Mock(spec=Settings)
        settings.github_token = "ghp_test_token_123"
        return settings
    
    def test_initialization_without_github_token(self, mock_settings_no_token):
        """Test initialization without GitHub authentication token."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            service = RunbookService(mock_settings_no_token)
            
            # Should store settings and create client
            assert service.settings == mock_settings_no_token
            assert service.client == mock_client_instance
            mock_client.assert_called_once()
            
            # Should set basic headers without authorization
            expected_headers = {
                "Accept": "application/vnd.github.v3.raw",
                "User-Agent": "Tarsy-bot/1.0"
            }
            assert service.headers == expected_headers
            assert "Authorization" not in service.headers
    
    def test_initialization_with_github_token(self, mock_settings_with_token):
        """Test initialization with GitHub authentication token."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            service = RunbookService(mock_settings_with_token)
            
            # Should store settings and create client
            assert service.settings == mock_settings_with_token
            assert service.client == mock_client_instance
            
            # Should set headers with authorization
            expected_headers = {
                "Accept": "application/vnd.github.v3.raw",
                "User-Agent": "Tarsy-bot/1.0",
                "Authorization": "token ghp_test_token_123"
            }
            assert service.headers == expected_headers
    
    def test_initialization_with_empty_github_token(self):
        """Test initialization with empty GitHub token."""
        settings = Mock(spec=Settings)
        settings.github_token = ""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            service = RunbookService(settings)
            
            # Empty token should be treated as no token
            assert "Authorization" not in service.headers
    
    def test_initialization_headers_structure(self, mock_settings_no_token):
        """Test that initialization creates proper headers structure."""
        with patch('httpx.AsyncClient'):
            service = RunbookService(mock_settings_no_token)
            
            # Should have required GitHub API headers
            assert "Accept" in service.headers
            assert "User-Agent" in service.headers
            assert service.headers["Accept"] == "application/vnd.github.v3.raw"
            assert service.headers["User-Agent"] == "Tarsy-bot/1.0"


@pytest.mark.unit
class TestURLConversion:
    """Test GitHub URL conversion to raw content URLs."""
    
    @pytest.fixture
    def service(self):
        """Create RunbookService instance for testing."""
        settings = Mock(spec=Settings)
        settings.github_token = None
        with patch('httpx.AsyncClient'):
            return RunbookService(settings)
    
    def test_convert_github_blob_url_to_raw(self, service):
        """Test converting GitHub blob URL to raw URL."""
        github_url = "https://github.com/user/repo/blob/master/docs/runbook.md"
        expected_raw_url = "https://raw.githubusercontent.com/user/repo/master/docs/runbook.md"
        
        result = service._convert_to_raw_url(github_url)
        assert result == expected_raw_url
    
    def test_convert_github_blob_url_with_branch(self, service):
        """Test converting GitHub blob URL with different branch."""
        github_url = "https://github.com/org/project/blob/develop/scripts/setup.sh"
        expected_raw_url = "https://raw.githubusercontent.com/org/project/develop/scripts/setup.sh"
        
        result = service._convert_to_raw_url(github_url)
        assert result == expected_raw_url
    
    def test_convert_github_blob_url_nested_path(self, service):
        """Test converting GitHub blob URL with nested file path."""
        github_url = "https://github.com/company/repo/blob/main/docs/ops/troubleshooting/k8s.md"
        expected_raw_url = "https://raw.githubusercontent.com/company/repo/main/docs/ops/troubleshooting/k8s.md"
        
        result = service._convert_to_raw_url(github_url)
        assert result == expected_raw_url
    
    def test_convert_already_raw_url(self, service):
        """Test that raw URLs are returned unchanged."""
        raw_url = "https://raw.githubusercontent.com/user/repo/master/file.md"
        
        result = service._convert_to_raw_url(raw_url)
        assert result == raw_url
    
    def test_convert_non_github_url(self, service):
        """Test that non-GitHub URLs are returned unchanged."""
        non_github_url = "https://example.com/docs/runbook.md"
        
        result = service._convert_to_raw_url(non_github_url)
        assert result == non_github_url
    
    def test_convert_malformed_github_url(self, service):
        """Test handling of malformed GitHub URLs."""
        malformed_urls = [
            "https://github.com/user",  # Missing repo
            "https://github.com/user/repo",  # Missing blob
            "https://github.com/user/repo/blob",  # Missing branch
            "https://github.com/user/repo/blob/master",  # Missing file
            "https://github.com/user/repo/tree/master/file.md",  # Tree instead of blob
        ]
        
        for url in malformed_urls:
            result = service._convert_to_raw_url(url)
            # Should return original URL when conversion fails
            assert result == url
    
    def test_convert_github_url_with_special_characters(self, service):
        """Test converting GitHub URLs with special characters in paths."""
        github_url = "https://github.com/user/repo/blob/feature/fix-bug/docs/run%20book.md"
        expected_raw_url = "https://raw.githubusercontent.com/user/repo/feature/fix-bug/docs/run%20book.md"
        
        result = service._convert_to_raw_url(github_url)
        assert result == expected_raw_url
    
    def test_convert_github_url_with_hash_branch(self, service):
        """Test converting GitHub URL with branch name containing hash."""
        github_url = "https://github.com/user/repo/blob/feature#123/file.md"
        expected_raw_url = "https://raw.githubusercontent.com/user/repo/feature#123/file.md"
        
        result = service._convert_to_raw_url(github_url)
        assert result == expected_raw_url
    
    def test_convert_empty_url(self, service):
        """Test handling of empty URL."""
        result = service._convert_to_raw_url("")
        assert result == ""
    
    def test_convert_none_url(self, service):
        """Test handling of None URL."""
        # Production code doesn't handle None input gracefully
        with pytest.raises(TypeError):
            service._convert_to_raw_url(None)


@pytest.mark.unit
class TestRunbookDownload:
    """Test runbook download functionality."""
    
    @pytest.fixture
    def service(self):
        """Create RunbookService instance with mocked client."""
        settings = Mock(spec=Settings)
        settings.github_token = "test_token"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            service = RunbookService(settings)
            return service
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        response = Mock()
        response.text = "# Runbook Content\n\nThis is a test runbook."
        response.raise_for_status = Mock()
        return response
    
    async def test_download_runbook_success(self, service, mock_response):
        """Test successful runbook download."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        expected_raw_url = "https://raw.githubusercontent.com/user/repo/master/runbook.md"
        
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(github_url)
        
        # Should convert URL and download content
        service.client.get.assert_called_once_with(expected_raw_url, headers=service.headers)
        mock_response.raise_for_status.assert_called_once()
        assert result == "# Runbook Content\n\nThis is a test runbook."
    
    async def test_download_runbook_already_raw_url(self, service, mock_response):
        """Test download with already raw GitHub URL."""
        raw_url = "https://raw.githubusercontent.com/user/repo/master/runbook.md"
        
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(raw_url)
        
        # Should use URL as-is
        service.client.get.assert_called_once_with(raw_url, headers=service.headers)
        assert result == "# Runbook Content\n\nThis is a test runbook."
    
    async def test_download_runbook_http_error(self, service):
        """Test download with HTTP error."""
        github_url = "https://github.com/user/repo/blob/master/nonexistent.md"
        
        http_error = httpx.HTTPStatusError(
            "404 Client Error: Not Found",
            request=Mock(),
            response=Mock()
        )
        service.client.get.side_effect = http_error
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
    
    async def test_download_runbook_network_error(self, service):
        """Test download with network error."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        
        network_error = httpx.NetworkError("Network connection failed")
        service.client.get.side_effect = network_error
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
    
    async def test_download_runbook_timeout_error(self, service):
        """Test download with timeout error."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        
        timeout_error = httpx.TimeoutException("Request timed out")
        service.client.get.side_effect = timeout_error
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
    
    async def test_download_runbook_response_status_error(self, service):
        """Test download when response indicates HTTP error status."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock()
        )
        service.client.get.return_value = mock_response
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
        
        # Should still call raise_for_status
        mock_response.raise_for_status.assert_called_once()
    
    async def test_download_runbook_headers_included(self, service, mock_response):
        """Test that proper headers are included in download request."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        expected_headers = {
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "Tarsy-bot/1.0",
            "Authorization": "token test_token"
        }
        
        service.client.get.return_value = mock_response
        
        await service.download_runbook(github_url)
        
        # Should include all configured headers
        call_args = service.client.get.call_args
        assert call_args[1]["headers"] == expected_headers
    
    async def test_download_runbook_empty_response(self, service):
        """Test download with empty response content."""
        github_url = "https://github.com/user/repo/blob/master/empty.md"
        
        mock_response = Mock()
        mock_response.text = ""
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(github_url)
        
        assert result == ""
    
    async def test_download_runbook_large_response(self, service):
        """Test download with large response content."""
        github_url = "https://github.com/user/repo/blob/master/large.md"
        large_content = "# Large Runbook\n" + "Content line\n" * 10000
        
        mock_response = Mock()
        mock_response.text = large_content
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(github_url)
        
        assert result == large_content
        assert len(result) > 100000  # Verify it's actually large
    
    async def test_download_runbook_unicode_content(self, service):
        """Test download with Unicode content."""
        github_url = "https://github.com/user/repo/blob/master/unicode.md"
        unicode_content = "# Runbook 🚀\n\nДокументация\n中文文档\n"
        
        mock_response = Mock()
        mock_response.text = unicode_content
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(github_url)
        
        assert result == unicode_content


@pytest.mark.unit
class TestAuthenticationHandling:
    """Test GitHub authentication handling."""
    
    async def test_download_without_authentication(self):
        """Test download without GitHub token."""
        settings = Mock(spec=Settings)
        settings.github_token = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_response = Mock()
            mock_response.text = "Public content"
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            
            service = RunbookService(settings)
            result = await service.download_runbook("https://github.com/user/repo/blob/master/public.md")
            
            # Should not include Authorization header
            call_args = mock_client_instance.get.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" not in headers
            assert headers["Accept"] == "application/vnd.github.v3.raw"
            assert headers["User-Agent"] == "Tarsy-bot/1.0"
            assert result == "Public content"
    
    async def test_download_with_authentication(self):
        """Test download with GitHub token."""
        settings = Mock(spec=Settings)
        settings.github_token = "ghp_secret_token"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            
            mock_response = Mock()
            mock_response.text = "Private content"
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            
            service = RunbookService(settings)
            result = await service.download_runbook("https://github.com/org/private/blob/master/secret.md")
            
            # Should include Authorization header
            call_args = mock_client_instance.get.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "token ghp_secret_token"
            assert result == "Private content"
    
    async def test_authentication_with_different_token_formats(self):
        """Test authentication with different token formats."""
        token_formats = [
            "ghp_standard_token_123",
            "github_pat_legacy_token",
            "gho_oauth_token_456",
            "simple_token"
        ]
        
        for token in token_formats:
            settings = Mock(spec=Settings)
            settings.github_token = token
            
            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_client.return_value = mock_client_instance
                
                service = RunbookService(settings)
                
                # Should format token correctly regardless of format
                assert service.headers["Authorization"] == f"token {token}"


@pytest.mark.unit
class TestResourceCleanup:
    """Test resource cleanup and lifecycle management."""
    
    @pytest.fixture
    def service(self):
        """Create RunbookService instance with mocked client."""
        settings = Mock(spec=Settings)
        settings.github_token = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            service = RunbookService(settings)
            return service
    
    async def test_close_client(self, service):
        """Test closing HTTP client."""
        await service.close()
        
        service.client.aclose.assert_called_once()
    
    async def test_close_client_with_exception(self, service):
        """Test closing client when aclose raises exception."""
        service.client.aclose.side_effect = Exception("Client close failed")
        
        # Production code doesn't catch exceptions in close()
        with pytest.raises(Exception, match="Client close failed"):
            await service.close()
        
        service.client.aclose.assert_called_once()
    
    async def test_close_client_already_closed(self, service):
        """Test closing client that's already closed."""
        # First close
        await service.close()
        service.client.aclose.assert_called_once()
        
        # Second close should work without issues
        await service.close()
        assert service.client.aclose.call_count == 2
    
    async def test_close_idempotent(self, service):
        """Test that close is idempotent."""
        # Multiple calls to close should not cause issues
        await service.close()
        await service.close()
        await service.close()
        
        assert service.client.aclose.call_count == 3


@pytest.mark.unit
class TestErrorScenariosAndEdgeCases:
    """Test error scenarios and edge cases."""
    
    @pytest.fixture
    def service(self):
        """Create RunbookService instance with mocked client."""
        settings = Mock(spec=Settings)
        settings.github_token = "test_token"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            service = RunbookService(settings)
            return service
    
    async def test_download_with_invalid_url_format(self, service):
        """Test download with various invalid URL formats."""
        invalid_urls = [
            "not-a-url",
            "ftp://github.com/user/repo/file.md", 
            "https://",
            "github.com/user/repo"  # Missing protocol
        ]
        
        for invalid_url in invalid_urls:
            # Should attempt to download even invalid URLs
            # The HTTP client will handle the actual error
            # Use HTTPError which is caught by the production code
            http_error = httpx.RequestError("Invalid URL")
            service.client.get.side_effect = http_error
            
            with pytest.raises(Exception, match="Failed to download runbook"):
                await service.download_runbook(invalid_url)
    
    async def test_download_with_connection_refused(self, service):
        """Test download when connection is refused."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        
        connection_error = httpx.ConnectError("Connection refused")
        service.client.get.side_effect = connection_error
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
    
    async def test_download_with_ssl_error(self, service):
        """Test download with SSL/TLS error."""
        github_url = "https://github.com/user/repo/blob/master/runbook.md"
        
        ssl_error = httpx.ConnectError("SSL: CERTIFICATE_VERIFY_FAILED")
        service.client.get.side_effect = ssl_error
        
        with pytest.raises(Exception, match="Failed to download runbook"):
            await service.download_runbook(github_url)
    
    async def test_url_conversion_with_edge_cases(self, service):
        """Test URL conversion with various edge cases."""
        edge_cases = [
            ("https://github.com/user/repo/blob/master/", "https://raw.githubusercontent.com/user/repo/master/"),
            ("https://github.com/user/repo/blob/feature-branch/deep/nested/path/file.md", 
             "https://raw.githubusercontent.com/user/repo/feature-branch/deep/nested/path/file.md"),
            ("https://github.com/user-name/repo-name/blob/branch-name/file-name.md",
             "https://raw.githubusercontent.com/user-name/repo-name/branch-name/file-name.md")
        ]
        
        for input_url, expected_output in edge_cases:
            result = service._convert_to_raw_url(input_url)
            assert result == expected_output
    
    async def test_concurrent_downloads(self, service):
        """Test handling of concurrent download requests."""
        import asyncio
        
        urls = [
            "https://github.com/user1/repo1/blob/master/file1.md",
            "https://github.com/user2/repo2/blob/master/file2.md",
            "https://github.com/user3/repo3/blob/master/file3.md"
        ]
        
        # Mock responses for each URL
        responses = []
        for i in range(len(urls)):
            response = Mock()
            response.text = f"Content for file{i+1}"
            response.raise_for_status = Mock()
            responses.append(response)
        
        service.client.get.side_effect = responses
        
        # Execute concurrent downloads
        tasks = [service.download_runbook(url) for url in urls]
        results = await asyncio.gather(*tasks)
        
        # Should handle concurrent requests correctly
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == f"Content for file{i+1}"
        
        # Should have made 3 HTTP requests
        assert service.client.get.call_count == 3


@pytest.mark.unit
class TestIntegrationScenarios:
    """Test integration scenarios and real-world usage patterns."""
    
    @pytest.fixture
    def service(self):
        """Create RunbookService instance with mocked client."""
        settings = Mock(spec=Settings)
        settings.github_token = "integration_test_token"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            service = RunbookService(settings)
            return service
    
    async def test_typical_runbook_download_flow(self, service):
        """Test typical runbook download flow as used by AlertService."""
        # Typical scenario: AlertService downloads runbook for processing
        runbook_url = "https://github.com/company/runbooks/blob/master/k8s/pod-restart.md"
        runbook_content = """
# Pod Restart Runbook

## Diagnosis Steps
1. Check pod status
2. Review logs
3. Check resource limits

## Resolution
- Restart deployment if needed
"""
        
        mock_response = Mock()
        mock_response.text = runbook_content
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(runbook_url)
        
        # Should successfully download and return content
        assert result == runbook_content
        assert "Pod Restart Runbook" in result
        assert "Diagnosis Steps" in result
        
        # Should convert URL and use proper headers
        expected_raw_url = "https://raw.githubusercontent.com/company/runbooks/master/k8s/pod-restart.md"
        service.client.get.assert_called_once_with(expected_raw_url, headers=service.headers)
    
    async def test_download_with_service_lifecycle(self, service):
        """Test download within service lifecycle (init -> use -> cleanup)."""
        # Service is already initialized in fixture
        
        # Use service for download
        mock_response = Mock()
        mock_response.text = "Runbook content"
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook("https://github.com/user/repo/blob/master/runbook.md")
        assert result == "Runbook content"
        
        # Cleanup service
        await service.close()
        service.client.aclose.assert_called_once()
    
    async def test_error_handling_in_integration_context(self, service):
        """Test error handling as it would be used by AlertService."""
        # Simulate scenario where runbook URL is invalid/inaccessible
        runbook_url = "https://github.com/user/repo/blob/master/missing-runbook.md"
        
        http_error = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=Mock()
        )
        service.client.get.side_effect = http_error
        
        # AlertService would catch this exception and handle gracefully
        with pytest.raises(Exception) as exc_info:
            await service.download_runbook(runbook_url)
        
        error_message = str(exc_info.value)
        assert "Failed to download runbook" in error_message
        assert runbook_url in error_message
    
    async def test_authentication_in_enterprise_context(self, service):
        """Test authentication handling in enterprise GitHub context."""
        # Enterprise GitHub with private repositories
        private_runbook_url = "https://github.com/enterprise/private-runbooks/blob/master/critical/incident.md"
        
        mock_response = Mock()
        mock_response.text = "# CONFIDENTIAL: Critical Incident Response"
        mock_response.raise_for_status = Mock()
        service.client.get.return_value = mock_response
        
        result = await service.download_runbook(private_runbook_url)
        
        # Should include authentication headers for private repo access
        call_args = service.client.get.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "token integration_test_token"
        assert result == "# CONFIDENTIAL: Critical Incident Response" 