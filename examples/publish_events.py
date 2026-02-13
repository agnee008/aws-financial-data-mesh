"""
publish_events.py - Example Script for Publishing Events

Demonstrates how to use the publishers to send events to EventBridge.

Author: Agnibes Banerjee
License: MIT
"""

import sys
import os
from decimal import Decimal
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from publishers.trade_publisher import TradeEventPublisher
from publishers.credit_publisher import CreditEventPublisher


def publish_sample_trades():
    """Publish sample trade events."""
    print("📊 Publishing sample trade events...")
    
    publisher = TradeEventPublisher(
        event_bus_name='financial-data-mesh-bus',
        region='eu-west-2'
    )
    
    # Sample trades
    trades = [
        {
            'trade_id': 'TRD0000001234',
            'instrument': 'AAPL',
            'quantity': 100,
            'price': Decimal('150.25'),
            'trader_id': 'TRD001',
            'direction': 'BUY',
            'exchange': 'NASDAQ'
        },
        {
            'trade_id': 'TRD0000001235',
            'instrument': 'GOOGL',
            'quantity': 50,
            'price': Decimal('2850.75'),
            'trader_id': 'TRD002',
            'direction': 'SELL',
            'exchange': 'NASDAQ'
        },
        {
            'trade_id': 'TRD0000001236',
            'instrument': 'MSFT',
            'quantity': 200,
            'price': Decimal('375.50'),
            'trader_id': 'TRD001',
            'direction': 'BUY',
            'exchange': 'NASDAQ'
        }
    ]
    
    for trade in trades:
        try:
            event_id = publisher.publish_trade(trade)
            print(f"✅ Published {trade['trade_id']}: {event_id}")
        except Exception as e:
            print(f"❌ Failed to publish {trade['trade_id']}: {e}")


def publish_sample_credits():
    """Publish sample credit decision events."""
    print("\n💳 Publishing sample credit decisions...")
    
    publisher = CreditEventPublisher(
        event_bus_name='financial-data-mesh-bus',
        region='eu-west-2'
    )
    
    # Sample credit decisions
    decisions = [
        {
            'application_id': 'APP0000001234',
            'customer_id': 'CUST0001',
            'credit_score': 750,
            'decision': 'APPROVED',
            'credit_limit': Decimal('50000.00'),
            'risk_category': 'LOW'
        },
        {
            'application_id': 'APP0000001235',
            'customer_id': 'CUST0002',
            'credit_score': 620,
            'decision': 'REVIEW_REQUIRED',
            'credit_limit': None,
            'risk_category': 'MEDIUM'
        }
    ]
    
    for decision in decisions:
        try:
            event_id = publisher.publish_decision(decision)
            print(f"✅ Published {decision['application_id']}: {event_id}")
        except Exception as e:
            print(f"❌ Failed to publish {decision['application_id']}: {e}")


def publish_batch_trades():
    """Publish a batch of trades."""
    print("\n📦 Publishing batch of trades...")
    
    publisher = TradeEventPublisher(
        event_bus_name='financial-data-mesh-bus',
        region='eu-west-2'
    )
    
    # Generate 25 sample trades
    batch_trades = [
        {
            'trade_id': f'TRD{str(i).zfill(10)}',
            'instrument': 'TSLA',
            'quantity': 100,
            'price': Decimal('245.50'),
            'trader_id': 'TRD003',
            'direction': 'BUY' if i % 2 == 0 else 'SELL',
            'exchange': 'NASDAQ'
        }
        for i in range(1000, 1025)
    ]
    
    try:
        event_ids = publisher.publish_batch(batch_trades)
        print(f"✅ Published batch of {len(event_ids)} trades")
    except Exception as e:
        print(f"❌ Failed to publish batch: {e}")


if __name__ == "__main__":
    print("🚀 AWS Financial Data Mesh - Event Publishing Examples\n")
    print("=" * 60)
    
    # Check for required environment variables
    required_env_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   Make sure AWS credentials are configured.")
        print("\nContinuing anyway (will use default credential chain)...\n")
    
    # Publish sample events
    publish_sample_trades()
    publish_sample_credits()
    publish_batch_trades()
    
    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("\nCheck EventBridge console to verify events were published.")
