# Main Routes

The router defines extensive nested routes for CRUD operations.

## Top-level Routes
- `/` (index)
- login, signup, register, forgotpassword-*
- virtualterminal, dashboard
- contacts/:id/* (dashboard, charge, emails, files, notes, paylinks, quickinvoices, recurrings, transactions, users, virtualterminal)
- locations/:id/* (add, view, accounts, billingstatements, contacts, dashboard, deviceterms, filecategories, files, hpp-*, marketplace, notes, notificationalerts, products, quickinvoices, reports-*, scanners, settings-*, tags, terminals, users, visibilitygroups)
- reports/* (ach-*, cc-*, transactions, recurrings, etc.)
- admin/* (addons, billingtiers, contacts, developercompanies, developers, domains, featureflags, helppages, roles, users, etc.)
- paylinks, quickinvoice, accounts, recurrings (standalone CRUD)
- mailboxmessagesuser, users

## Examples
- `/contacts/:id/paylinks/:paylink_id` - Edit paylink for contact
- `/locations/:id/users/:user_id/preferences` - User prefs
- `/admin/users/:id/authroles` - Admin user roles

Full map in `app/router.js`.
