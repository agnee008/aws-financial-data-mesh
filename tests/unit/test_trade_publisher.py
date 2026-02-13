"""
test_trade_publisher.py - Unit tests for TradeEventPublisher

Author: Agnibes Banerjee
License: MIT
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from src.publishers.trade_publisher import TradeEventPublisher, TradeEvent


class TestTradeEvent:
    """Tests for TradeEvent dataclass."""
    
    def test_valid_trade_event(self):
        """Test creating a valid trade event."""
        trade = TradeEvent(
            trade_id='TRD0000001234',
            instrument='AAPL',
            quantity=100,
            price=Decimal('150.25'),
            trader_id='TRD001',
            timestamp='2026-02-13T10:30:00Z',
            direction='BUY',
            exchange='NASDAQ'
        )
        
        assert trade.trade_id == 'TRD0000001234'
        assert trade.instrument == 'AAPL'
        assert trade.quantity == 100
        assert trade.price == Decimal('150.25')
    
    def test_invalid_trade_id(self):
        """Test that invalid trade_id raises error."""
        with pytest.raises(ValueError, match="trade_id must start with 'TRD'"):
            TradeEvent(
                trade_id='INVALID',
                instrument='AAPL',
                quantity=100,
                price=Decimal('150.25'),
                trader_id='TRD001',
                timestamp='2026-02-13T10:30:00Z',
                direction='BUY',
                exchange='NASDAQ'
            )
    
    def test_invalid_quantity(self):
        """Test that negative quantity raises error."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            TradeEvent(
                trade_id='TRD0000001234',
                instrument='AAPL',
                quantity=-100,
                price=Decimal('150.25'),
                trader_id='TRD001',
                timestamp='2026-02-13T10:30:00Z',
                direction='BUY',
                exchange='NASDAQ'
            )
    
    def test_invalid_direction(self):
        """Test that invalid direction raises error."""
        with pytest.raises(ValueError, match="direction must be BUY or SELL"):
            TradeEvent(
                trade_id='TRD0000001234',
                instrument='AAPL',
                quantity=100,
                price=Decimal('150.25'),
                trader_id='TRD001',
                timestamp='2026-02-13T10:30:00Z',
                direction='INVALID',
                exchange='NASDAQ'
            )


class TestTradeEventPublisher:
    """Tests for TradeEventPublisher."""
    
    @patch('src.publishers.trade_publisher.boto3')
    def test_publish_trade_success(self, mock_boto3):
        """Test successful trade publication."""
        # Mock EventBridge client
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_client.put_events.return_value = {
            'FailedEntryCount': 0,
            'Entries': [{'EventId': 'test-event-id'}]
        }
        
        publisher = TradeEventPublisher()
        
        trade_data = {
            'trade_id': 'TRD0000001234',
            'instrument': 'AAPL',
            'quantity': 100,
            'price': Decimal('150.25'),
            'trader_id': 'TRD001',
            'direction': 'BUY',
            'exchange': 'NASDAQ'
        }
        
        event_id = publisher.publish_trade(trade_data)
        
        assert event_id == 'test-event-id'
        mock_client.put_events.assert_called_once()
    
    @patch('src.publishers.trade_publisher.boto3')
    def test_publish_trade_failure(self, mock_boto3):
        """Test failed trade publication."""
        # Mock EventBridge client
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_client.put_events.return_value = {
            'FailedEntryCount': 1,
            'Entries': [{'ErrorMessage': 'Test error'}]
        }
        
        publisher = TradeEventPublisher()
        
        trade_data = {
            'trade_id': 'TRD0000001234',
            'instrument': 'AAPL',
            'quantity': 100,
            'price': Decimal('150.25'),
            'trader_id': 'TRD001',
            'direction': 'BUY',
            'exchange': 'NASDAQ'
        }
        
        with pytest.raises(Exception, match="Failed to publish event"):
            publisher.publish_trade(trade_data)
    
    @patch('src.publishers.trade_publisher.boto3')
    def test_publish_batch(self, mock_boto3):
        """Test batch publication."""
        # Mock EventBridge client
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_client.put_events.return_value = {
            'FailedEntryCount': 0,
            'Entries': [
                {'EventId': 'event-1'},
                {'EventId': 'event-2'}
            ]
        }
        
        publisher = TradeEventPublisher()
        
        trades = [
            {
                'trade_id': f'TRD{str(i).zfill(10)}',
                'instrument': 'AAPL',
                'quantity': 100,
                'price': Decimal('150.25'),
                'trader_id': 'TRD001',
                'direction': 'BUY',
                'exchange': 'NASDAQ'
            }
            for i in range(2)
        ]
        
        event_ids = publisher.publish_batch(trades)
        
        assert len(event_ids) == 2
        assert event_ids == ['event-1', 'event-2']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
