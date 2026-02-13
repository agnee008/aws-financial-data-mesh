"""
schema_validator.py - Lambda Function for Event Schema Validation

Validates incoming events against JSON schemas.

Author: Agnibes Banerjee
License: MIT
"""

import json
import os
from typing import Dict, Any
import logging
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Trade event schema
TRADE_SCHEMA = {
    "type": "object",
    "required": ["trade_id", "instrument", "quantity", "price", "trader_id", "direction"],
    "properties": {
        "trade_id": {
            "type": "string",
            "pattern": "^TRD[0-9]{10}$"
        },
        "instrument": {
            "type": "string",
            "minLength": 1,
            "maxLength": 10
        },
        "quantity": {
            "type": "number",
            "minimum": 1
        },
        "price": {
            "type": "number",
            "minimum": 0.01
        },
        "trader_id": {
            "type": "string",
            "pattern": "^TRD[0-9]{3}$"
        },
        "direction": {
            "type": "string",
            "enum": ["BUY", "SELL"]
        },
        "exchange": {
            "type": "string"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        }
    }
}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for schema validation.
    
    Args:
        event: EventBridge event
        context: Lambda context
        
    Returns:
        Validation result
    """
    logger.info(f"Validating event: {event.get('detail-type')}")
    
    detail = event.get('detail', {})
    detail_type = event.get('detail-type')
    
    # Select appropriate schema based on event type
    if detail_type == 'TradeExecuted':
        schema = TRADE_SCHEMA
    else:
        logger.warning(f"No schema defined for event type: {detail_type}")
        return {
            'statusCode': 200,
            'validation': 'SKIPPED',
            'reason': 'No schema defined'
        }
    
    # Validate event
    try:
        validate(instance=detail, schema=schema)
        logger.info(f"✅ Validation successful for {detail.get('trade_id')}")
        
        return {
            'statusCode': 200,
            'validation': 'SUCCESS',
            'event_id': detail.get('trade_id')
        }
        
    except ValidationError as e:
        logger.error(f"❌ Validation failed: {str(e)}")
        
        return {
            'statusCode': 400,
            'validation': 'FAILED',
            'error': str(e),
            'path': list(e.path),
            'event_id': detail.get('trade_id', 'UNKNOWN')
        }
    
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        
        return {
            'statusCode': 500,
            'validation': 'ERROR',
            'error': str(e)
        }


def validate_schema_strict(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, str]:
    """
    Strict schema validation with detailed error messages.
    
    Args:
        data: Data to validate
        schema: JSON schema
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    
    if not errors:
        return True, ""
    
    error_messages = []
    for error in errors:
        path = " -> ".join(str(p) for p in error.path)
        error_messages.append(f"{path}: {error.message}")
    
    return False, "; ".join(error_messages)
