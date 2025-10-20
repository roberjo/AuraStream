"""AWS service clients configuration."""

import boto3
from botocore.config import Config
from typing import Any, Dict


class AWSClientManager:
    """Manages AWS service clients with optimized configuration."""

    def __init__(self, region: str = "us-east-1"):
        """Initialize AWS client manager."""
        self.region = region
        self._config = Config(
            max_pool_connections=100,
            retries={"max_attempts": 3, "mode": "adaptive"},
            read_timeout=30,
            connect_timeout=10,
        )
        self._clients: Dict[str, Any] = {}

    def get_comprehend_client(self) -> Any:
        """Get Amazon Comprehend client."""
        if "comprehend" not in self._clients:
            self._clients["comprehend"] = boto3.client(
                "comprehend", region_name=self.region, config=self._config
            )
        return self._clients["comprehend"]

    def get_dynamodb_resource(self) -> Any:
        """Get DynamoDB resource."""
        if "dynamodb" not in self._clients:
            self._clients["dynamodb"] = boto3.resource(
                "dynamodb", region_name=self.region, config=self._config
            )
        return self._clients["dynamodb"]

    def get_s3_client(self) -> Any:
        """Get S3 client."""
        if "s3" not in self._clients:
            self._clients["s3"] = boto3.client(
                "s3", region_name=self.region, config=self._config
            )
        return self._clients["s3"]

    def get_stepfunctions_client(self) -> Any:
        """Get Step Functions client."""
        if "stepfunctions" not in self._clients:
            self._clients["stepfunctions"] = boto3.client(
                "stepfunctions", region_name=self.region, config=self._config
            )
        return self._clients["stepfunctions"]


# Global client manager instance
aws_clients = AWSClientManager()
