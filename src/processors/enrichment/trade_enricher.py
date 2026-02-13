"""
trade_enricher.py - Lambda Function for Trade Event Enrichment

Enriches trade events with instrument metadata from DynamoDB.

Author: Agnibes Banerjee
License: MIT
"""

import json
import os
import boto3
from typing import Dict, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

# Environment variables
INSTRUMENTS_TABLE = os.environ.get('INSTRUMENTS_TABLE', 'instruments-reference')
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'financial-data-mesh-bus')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for enriching trade events.
    
    Args:
        event: SQS event containing trade records
        context: Lambda context
        
    Returns:
        Processing result
    """
    logger.info(f"Processing {len(event['Records'])} trade events")
    
    table = dynamodb.Table(INSTRUMENTS_TABLE)
    enriched_count = 0
    failed_count = 0
    
    for record in event['Records']:
        try:
            # Parse trade event from SQS message
            trade = json.loads(record['body'])
            instrument_code = trade.get('instrument')
            
            if not instrument_code:
                logger.warning(f"Missing instrument code in trade: {trade.get('trade_id')}")
                failed_count += 1
                continue
            
            # Fetch instrument metadata from DynamoDB
            response = table.get_item(Key={'instrument_code': instrument_code})
            
            if 'Item' not in response:
                logger.warning(f"Instrument not found: {instrument_code}")
                # Continue with partial enrichment
                instrument_metadata = {
                    'sector': 'UNKNOWN',
                    'currency': 'USD',
                    'exchange': 'UNKNOWN'
                }
            else:
                instrument_metadata = {
                    'sector': response['Item'].get('sector', 'UNKNOWN'),
                    'currency': response['Item'].get('currency', 'USD'),
                    'exchange': response['Item'].get('exchange', 'UNKNOWN'),
                    'market_cap': response['Item'].get('market_cap'),
                    'industry': response['Item'].get('industry')
                }
            
            # Enrich the trade event
            enriched_trade = {
                **trade,
                'instrument_metadata': instrument_metadata,
                'enrichment_timestamp': context.aws_request_id
            }
            
            # Publish enriched event to EventBridge
            publish_enriched_event(enriched_trade)
            enriched_count += 1
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            failed_count += 1
    
    logger.info(f"Enrichment complete. Success: {enriched_count}, Failed: {failed_count}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'enriched': enriched_count,
            'failed': failed_count
        })
    }


def publish_enriched_event(trade: Dict[str, Any]) -> str:
    """
    Publish enriched trade event to EventBridge.
    
    Args:
        trade: Enriched trade data
        
    Returns:
        EventBridge event ID
    """
    event_entry = {
        'Source': 'enrichment.trade',
        'DetailType': 'TradeEnriched',
        'Detail': json.dumps(trade),
        'EventBusName': EVENT_BUS_NAME
    }
    
    response = eventbridge.put_events(Entries=[event_entry])
    
    if response['FailedEntryCount'] > 0:
        raise Exception(f"Failed to publish enriched event: {response}")
    
    return response['Entries'][0]['EventId']
