# Ember Data Models

Numerous models for API entities:

- **Core**: contact.js, location.js, user.js, transaction.js, accountvault.js, recurring.js, quickinvoice.js, paylink.js
- **Admin**: admin_* (e.g., admin_user.js, admin_billingtier.js)
- **Products/Services**: producttransaction.js, productrecurring.js, productaccountvault.js, productfile.js
- **Billing**: billingtier.js, billingstatement.js, locationbillingaccount.js
- **Reports**: transactionsummaryach.js, developersummaryreport.js, portfoliodetailsonboardingreport.js
- **Devices/Terminals**: terminal.js, scanner.js, terminalrouter.js, deviceterm.js
- **Other**: featureflag.js, notificationtemplate.js, postbackconfig.js, visibilitygroup.js, marketplace.js

Full list available via `ls app/models/`. Models use RESTAdapter (inferred from setup).
