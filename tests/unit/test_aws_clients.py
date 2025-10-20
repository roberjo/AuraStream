"""Tests for AWS clients."""

from unittest.mock import Mock, patch

from src.utils.aws_clients import AWSClientManager, aws_clients


class TestAWSClientManager:
    """Test AWS client manager functionality."""

    def test_init_default_region(self):
        """Test initialization with default region."""
        manager = AWSClientManager()
        assert manager.region == "us-east-1"
        assert len(manager._clients) == 0

    def test_init_custom_region(self):
        """Test initialization with custom region."""
        manager = AWSClientManager("eu-west-1")
        assert manager.region == "eu-west-1"

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_comprehend_client(self, mock_boto_client):
        """Test getting Comprehend client."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager("us-west-2")
        client = manager.get_comprehend_client()

        assert client == mock_client
        mock_boto_client.assert_called_once_with(
            "comprehend", region_name="us-west-2", config=manager._config
        )

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_comprehend_client_cached(self, mock_boto_client):
        """Test getting Comprehend client returns cached instance."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager()
        client1 = manager.get_comprehend_client()
        client2 = manager.get_comprehend_client()

        assert client1 == client2
        mock_boto_client.assert_called_once()

    @patch("src.utils.aws_clients.boto3.resource")
    def test_get_dynamodb_resource(self, mock_boto_resource):
        """Test getting DynamoDB resource."""
        mock_resource = Mock()
        mock_boto_resource.return_value = mock_resource

        manager = AWSClientManager("eu-central-1")
        resource = manager.get_dynamodb_resource()

        assert resource == mock_resource
        mock_boto_resource.assert_called_once_with(
            "dynamodb", region_name="eu-central-1", config=manager._config
        )

    @patch("src.utils.aws_clients.boto3.resource")
    def test_get_dynamodb_resource_cached(self, mock_boto_resource):
        """Test getting DynamoDB resource returns cached instance."""
        mock_resource = Mock()
        mock_boto_resource.return_value = mock_resource

        manager = AWSClientManager()
        resource1 = manager.get_dynamodb_resource()
        resource2 = manager.get_dynamodb_resource()

        assert resource1 == resource2
        mock_boto_resource.assert_called_once()

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_s3_client(self, mock_boto_client):
        """Test getting S3 client."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager("ap-southeast-1")
        client = manager.get_s3_client()

        assert client == mock_client
        mock_boto_client.assert_called_once_with(
            "s3", region_name="ap-southeast-1", config=manager._config
        )

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_s3_client_cached(self, mock_boto_client):
        """Test getting S3 client returns cached instance."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager()
        client1 = manager.get_s3_client()
        client2 = manager.get_s3_client()

        assert client1 == client2
        mock_boto_client.assert_called_once()

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_stepfunctions_client(self, mock_boto_client):
        """Test getting Step Functions client."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager("ca-central-1")
        client = manager.get_stepfunctions_client()

        assert client == mock_client
        mock_boto_client.assert_called_once_with(
            "stepfunctions", region_name="ca-central-1", config=manager._config
        )

    @patch("src.utils.aws_clients.boto3.client")
    def test_get_stepfunctions_client_cached(self, mock_boto_client):
        """Test getting Step Functions client returns cached instance."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        manager = AWSClientManager()
        client1 = manager.get_stepfunctions_client()
        client2 = manager.get_stepfunctions_client()

        assert client1 == client2
        mock_boto_client.assert_called_once()

    def test_config_properties(self):
        """Test that config has expected properties."""
        manager = AWSClientManager()
        config = manager._config

        assert config.max_pool_connections == 100
        assert config.retries["max_attempts"] == 3
        assert config.retries["mode"] == "adaptive"
        assert config.read_timeout == 30
        assert config.connect_timeout == 10

    def test_multiple_clients_caching(self):
        """Test that multiple clients are cached independently."""
        with patch("src.utils.aws_clients.boto3.client") as mock_boto_client, patch(
            "src.utils.aws_clients.boto3.resource"
        ) as mock_boto_resource:
            mock_client = Mock()
            mock_resource = Mock()
            mock_boto_client.return_value = mock_client
            mock_boto_resource.return_value = mock_resource

            manager = AWSClientManager()

            # Get all clients
            comprehend = manager.get_comprehend_client()
            s3 = manager.get_s3_client()
            stepfunctions = manager.get_stepfunctions_client()
            dynamodb = manager.get_dynamodb_resource()

            # Verify all are cached
            assert len(manager._clients) == 4
            assert "comprehend" in manager._clients
            assert "s3" in manager._clients
            assert "stepfunctions" in manager._clients
            assert "dynamodb" in manager._clients

            # Verify they're the same instances
            assert manager.get_comprehend_client() == comprehend
            assert manager.get_s3_client() == s3
            assert manager.get_stepfunctions_client() == stepfunctions
            assert manager.get_dynamodb_resource() == dynamodb


class TestGlobalAWSClient:
    """Test global AWS client instance."""

    def test_global_instance_exists(self):
        """Test that global instance exists."""
        assert aws_clients is not None
        assert isinstance(aws_clients, AWSClientManager)

    def test_global_instance_default_region(self):
        """Test that global instance has default region."""
        assert aws_clients.region == "us-east-1"

    @patch("src.utils.aws_clients.boto3.client")
    def test_global_instance_functionality(self, mock_boto_client):
        """Test that global instance works correctly."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        client = aws_clients.get_comprehend_client()

        assert client == mock_client
        mock_boto_client.assert_called_once_with(
            "comprehend", region_name="us-east-1", config=aws_clients._config
        )
