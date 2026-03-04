# Directory Structure

Standard Ember.js structure:

```
ui/
├── app/
│   ├── components/     # Reusable UI components
│   ├── controllers/    # Route controllers
│   ├── helpers/
│   ├── models/         # Ember Data models (e.g., transaction.js, contact.js, location.js, user.js)
│   ├── routes/         # Route definitions (e.g., locations/, contacts/, admin/)
│   ├── router.js       # Main router map
│   ├── services/       # Services (e.g., authenticators)
│   ├── templates/      # Handlebars templates (.hbs)
│   └── ... (styles, util, etc.)
├── config/
│   └── environment.js  # Env-specific config (API URLs, CSP, etc.)
├── public/             # Static assets
├── tests/
├── package.json        # Dependencies
├── ember-cli-build.js
├── serverless.yml      # Deployment configs (dev, prod, sandbox)
├── docker-compose.yml
├── README.md
└── ... (mobile: corber/, PaymentSDKPlugin/, builds: Fortis.ipa)
```

Key subdirs in app/routes: locations, contacts, admin, reports, etc. (nested CRUD routes).

Many models (~100+): accountvault.js, billingtier.js, contact.js, location.js, paylink.js, producttransaction.js, quickinvoice.js, recurring.js, transaction.js, user.js, etc.
