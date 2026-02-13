"""
credit_publisher.py - Event Publisher for Credit Decision Events

Publishes credit assessment and decision events to AWS EventBridge.

Author: Agnibes Banerjee
License: MIT
"""

import boto3
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CreditEvent:
    """Credit decision event schema."""
    application_id: str
    customer_id: str
    credit_score: int
    decision: str  # APPROVED, REJECTED, REVIEW_REQUIRED
    credit_limit: Optional[Decimal]
    timestamp: str
    risk_category: str
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate credit event fields"""
        if self.decision not in ['APPROVED', 'REJECTED', 'REVIEW_REQUIRED']:
            raise ValueError("decision must be APPROVED, REJECTED, or REVIEW_REQUIRED")
        if self.credit_score < 300 or self.credit_score > 850:
            raise ValueError("credit_score must be between 300 and 850")


class CreditEventPublisher:
    """Publisher for credit decision events."""
    
    def __init__(
        self,
        event_bus_name: str = 'financial-data-mesh-bus',
        region: str = 'eu-west-2',
        source: str = 'credit.assessment'
    ):
        self.event_bus_name = event_bus_name
        self.source = source
        self.client = boto3.client('events', region_name=region)
        logger.info(f"Initialized CreditEventPublisher for bus: {event_bus_name}")
    
    def publish_decision(
        self,
        credit_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish a credit decision event."""
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        if 'timestamp' not in credit_data:
            credit_data['timestamp'] = datetime.utcnow().isoformat()
        
        credit_event = CreditEvent(
            correlation_id=correlation_id,
            **credit_data
        )
        
        event_entry = {
            'Source': self.source,
            'DetailType': 'CreditDecisionMade',
            'Detail': json.dumps(
                asdict(credit_event),
                default=self._decimal_serializer
            ),
            'EventBusName': self.event_bus_name
        }
        
        response = self.client.put_events(Entries=[event_entry])
        
        if response['FailedEntryCount'] > 0:
            error_msg = response['Entries'][0].get('ErrorMessage', 'Unknown error')
            raise Exception(f"Failed to publish event: {error_msg}")
        
        event_id = response['Entries'][0]['EventId']
        logger.info(f"Published credit decision {credit_event.application_id} with EventId: {event_id}")
        return event_id
    
    @staticmethod
    def _decimal_serializer(obj):
        """JSON serializer for Decimal objects"""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


if __name__ == "__main__":
    publisher = CreditEventPublisher()
    
    credit = {
        'application_id': 'APP0000001234',
        'customer_id': 'CUST0001',
        'credit_score': 750,
        'decision': 'APPROVED',
        'credit_limit': Decimal('50000.00'),
        'risk_category': 'LOW'
    }
    
    event_id = publisher.publish_decision(credit)
    print(f"✅ Published credit decision: {event_id}")
