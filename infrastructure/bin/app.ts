#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { EventBusStack } from '../lib/event-bus-stack';

const app = new cdk.App();

// Get configuration from context
const environment = app.node.tryGetContext('environment') || 'dev';
const eventBusName = app.node.tryGetContext('eventBusName') || 'financial-data-mesh-bus';

// Stack configuration
const stackProps: cdk.StackProps = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'eu-west-2',
  },
  description: 'AWS Financial Data Mesh - Event-Driven Architecture'
};

// Create EventBridge stack
new EventBusStack(app, `DataMeshStack-${environment}`, {
  ...stackProps,
  eventBusName,
  environment
});

app.synth();
