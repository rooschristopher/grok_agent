# Fortis UI Repository Documentation

## Overview
The `ui` repository is a web-based application built with **Ember.js** (version 3.28, Octane edition) that provides a user interface for interacting with the Zeamster/Fortis API. It enables users to perform payment-related actions based on their roles and privileges.

### Main Features
- Run Transactions
- Manage Contacts & Users
- Manage Account Vaults
- Recurring Billings
- Quick Invoices
- Managing Locations & their Services

### Tech Stack
- **Frontend Framework**: Ember.js 3.28.12
- **Data Layer**: Ember Data 3.28.7
- **Authentication**: Ember Simple Auth 6.0.0
- **Charts**: Highcharts 11.4.6
- **Other**: jQuery, Moment.js, Socket.io-client, ConfigCat for feature flags
- **Build Tools**: Ember CLI 3.28.6, Webpack, Serverless Framework for deployment
- **Mobile**: Corber for hybrid apps, SigPad for signatures, Android/iOS builds present (Fortis.ipa)

### API Integration
- API Namespace: `v2` (user), `v2admin` (admin)
- Multiple environments: development, sandbox, production, beta, etc.
- Cross-origin whitelists for various domains like api.zeamster.com, api.fortispay.com

### Deployment
Uses Serverless Framework (serverless.yml variants for dev, prod, sandbox). Supports Docker, AWS Lambda via serverless-lift.

## Quick Start (from original README)
1. Clone repo
2. `npm install`
3. `ember server --ssl=true --environment=development`
4. Update `config/environment.js` for dev URL if needed
5. Visit https://localhost:4200

