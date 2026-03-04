# Deployment

## Local Development
```
ember server --ssl=true --environment=development
```

## Serverless Deploy (e.g., Development)
```
rm -rf dist/*
npm install
ember build --environment developtest --output-path \"dist/developtest\"
serverless deploy --aws-profile zeamster-developer-terraform
```

Variants: serverless-dev.yml, serverless-prod.yml, serverless-sandbox.yml, etc.

## Docker
Dockerfile_qa, docker-compose.yml present.

Environments: development, sandbox, production, beta, ipaysandbox, etc. Configured in environment.js.
