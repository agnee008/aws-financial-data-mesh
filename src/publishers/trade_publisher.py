"""
trade_publisher.py - Event Publisher for Trade Execution Events

This module publishes trade execution events to AWS EventBridge,
implementing the Event-Driven Data Mesh pattern for financial services.

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeEvent:
    """
    Trade execution event schema.
    
    Attributes:
        trade_id: Unique trade identifier (format: TRD0000000001)
        instrument: Trading instrument code (e.g., AAPL, GOOGL)
        quantity: Number of shares/units
        price: Execution price
        trader_id: Trader identifier
        timestamp: ISO 8601 timestamp
        direction: BUY or SELL
        exchange: Trading venue
    """
    trade_id: str
    instrument: str
    quantity: int
    price: Decimal
    trader_id: str
    timestamp: str
    direction: str
    exchange: str
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade event fields"""
        if not self.trade_id.startswith('TRD'):
            raise ValueError("trade_id must start with 'TRD'")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.direction not in ['BUY', 'SELL']:
            raise ValueError("direction must be BUY or SELL")


class TradeEventPublisher:
    """
    Publisher for trade execution events.
    
    Publishes validated trade events to AWS EventBridge custom event bus.
    Implements retry logic, error handling, and correlation tracking.
    """
    
    def __init__(
        self,
        event_bus_name: str = 'financial-data-mesh-bus',
        region: str = 'eu-west-2',
        source: str = 'investment.trading'
    ):
        """
        Initialize the trade event publisher.
        
        Args:
            event_bus_name: Name of the EventBridge custom bus
            region: AWS region
            source: Event source identifier (Data Mesh domain)
        """
        self.event_bus_name = event_bus_name
        self.source = source
        self.client = boto3.client('events', region_name=region)
        logger.info(f"Initialized TradeEventPublisher for bus: {event_bus_name}")
    
    def publish_trade(
        self,
        trade_data: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Publish a trade execution event.
        
        Args:
            trade_data: Dictionary containing trade details
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            EventBridge event ID
            
        Raises:
            ValueError: If trade_data is invalid
            Exception: If EventBridge publish fails
            
        Example:
            >>> publisher = TradeEventPublisher()
            >>> trade = {
            ...     'trade_id': 'TRD0000001234',
            ...     'instrument': 'AAPL',
            ...     'quantity': 100,
            ...     'price': 150.25,
            ...     'trader_id': 'TRD001',
            ...     'direction': 'BUY',
            ...     'exchange': 'NASDAQ'
            ... }
            >>> event_id = publisher.publish_trade(trade)
        """
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add timestamp if not present
        if 'timestamp' not in trade_data:
            trade_data['timestamp'] = datetime.utcnow().isoformat()
        
        # Validate trade event
        try:
            trade_event = TradeEvent(
                correlation_id=correlation_id,
                **trade_data
            )
        except TypeError as e:
            raise ValueError(f"Invalid trade data: {e}")
        
        # Construct EventBridge event
        event_entry = {
            'Source': self.source,
            'DetailType': 'TradeExecuted',
            'Detail': json.dumps(
                asdict(trade_event),
                default=self._decimal_serializer
            ),
            'EventBusName': self.event_bus_name,
            'Resources': [
                f'arn:aws:trading:instrument:{trade_event.instrument}',
                f'arn:aws:trading:trader:{trade_event.trader_id}'
            ]
        }
        
        # Publish to EventBridge
        try:
            response = self.client.put_events(Entries=[event_entry])
            
            # Check for failures
            if response['FailedEntryCount'] > 0:
                error_msg = response['Entries'][0].get('ErrorMessage', 'Unknown error')
                raise Exception(f"Failed to publish event: {error_msg}")
            
            event_id = response['Entries'][0]['EventId']
            logger.info(
                f"Published trade event {trade_event.trade_id} "
                f"with EventId: {event_id}"
            )
            return event_id
            
        except Exception as e:
            logger.error(f"Error publishing trade event: {e}")
            raise
    
    def publish_batch(
        self,
        trades: list[Dict[str, Any]],
        correlation_id: Optional[str] = None
    ) -> list[str]:
        """
        Publish multiple trade events in a batch.
        
        EventBridge supports up to 10 events per PutEvents call.
        This method handles automatic batching for larger lists.
        
        Args:
            trades: List of trade dictionaries
            correlation_id: Optional correlation ID for the batch
            
        Returns:
            List of EventBridge event IDs
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        event_ids = []
        batch_size = 10
        
        for i in range(0, len(trades), batch_size):
            batch = trades[i:i + batch_size]
            entries = []
            
            for trade in batch:
                if 'timestamp' not in trade:
                    trade['timestamp'] = datetime.utcnow().isoformat()
                
                trade_event = TradeEvent(
                    correlation_id=f"{correlation_id}-{i}",
                    **trade
                )
                
                entries.append({
                    'Source': self.source,
                    'DetailType': 'TradeExecuted',
                    'Detail': json.dumps(
                        asdict(trade_event),
                        default=self._decimal_serializer
                    ),
                    'EventBusName': self.event_bus_name
                })
            
            response = self.client.put_events(Entries=entries)
            
            if response['FailedEntryCount'] > 0:
                logger.warning(
                    f"Batch had {response['FailedEntryCount']} failures"
                )
            
            batch_event_ids = [
                entry['EventId'] 
                for entry in response['Entries'] 
                if 'EventId' in entry
            ]
            event_ids.extend(batch_event_ids)
        
        logger.info(f"Published {len(event_ids)} trade events in batch")
        return event_ids
    
    @staticmethod
    def _decimal_serializer(obj):
        """JSON serializer for Decimal objects"""
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Example usage
if __name__ == "__main__":
    # Initialize publisher
    publisher = TradeEventPublisher()
    
    # Single trade example
    single_trade = {
        'trade_id': 'TRD0000001234',
        'instrument': 'AAPL',
        'quantity': 100,
        'price': Decimal('150.25'),
        'trader_id': 'TRD001',
        'direction': 'BUY',
        'exchange': 'NASDAQ'
    }
    
    try:
        event_id = publisher.publish_trade(single_trade)
        print(f"✅ Published trade: {event_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Batch example
    batch_trades = [
        {
            'trade_id': f'TRD{str(i).zfill(10)}',
            'instrument': 'GOOGL',
            'quantity': 50,
            'price': Decimal('2800.50'),
            'trader_id': 'TRD002',
            'direction': 'BUY',
            'exchange': 'NASDAQ'
        }
        for i in range(1, 25)  # 24 trades
    ]
    
    try:
        event_ids = publisher.publish_batch(batch_trades)
        print(f"✅ Published {len(event_ids)} trades in batch")
    except Exception as e:
        print(f"❌ Error: {e}")
