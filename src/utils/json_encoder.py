"""Custom JSON encoder for datetime objects and other non-serializable types."""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


class AuraStreamJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for AuraStream API responses."""

    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, "model_dump"):
            # Pydantic v2 models
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            # Legacy Pydantic models
            return obj.dict()
        return super().default(obj)


def json_dumps(obj: Any, **kwargs: Any) -> str:
    """JSON dumps with custom encoder."""
    return json.dumps(obj, cls=AuraStreamJSONEncoder, **kwargs)
