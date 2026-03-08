# Docker Compose Deployment Strategies for FSM-based User Authentication Service

## Introduction

Deploying a Finite State Machine (FSM)-based User Authentication Service using Docker Compose provides a robust, scalable, and maintainable solution for handling complex authentication flows. The FSM manages states such as `pending_registration`, `email_verified`, `mfa_enrolled`, `authenticated`, and `locked`, ensuring predictable transitions and state persistence. This guide covers multi-container setups, persistence strategies, networking, configuration via environment variables, scaling, health monitoring tailored to FSM states, visual diagrams, production migration paths, and security best practices.

The architecture typically includes:
- **auth-app**: The core service implementing FSM logic (e.g., using libraries like `transitions` in Python or `xstate` in Node.js).
- **postgres**: Relational database for persistent user data (profiles, credential hashes).
- **redis**: In-memory store for transient FSM states and sessions, enabling fast lookups and automatic expiration.

This setup ensures high availability, data durability, and efficient state management.

## Multi-Container Setup

Docker Compose orchestrates multiple services interacting seamlessly. The `auth-app` depends on `postgres` and `redis`, starting only after they are healthy. Communication occurs over a shared Docker network.

## Example `docker-compose.yml`

```yaml
version: '3.8'

services:
  auth-app:
    build:
      context: .
      dockerfile: Dockerfile.app
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://authuser:authpass@postgres:5432/authdb
      - REDIS_URL=redis://redis:6379/0
      - FSM_STATE_TTL=3600  # 1 hour TTL for FSM states
      - FSM_MAX_CONCURRENT_STATES=10000
      - JWT_SECRET=supersecretkeychangeinprod
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs  # For container logs
    networks:
      - auth-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: authdb
      POSTGRES_USER: authuser
      POSTGRES_PASSWORD: authpass
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - auth-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U authuser -d authdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data
    networks:
      - auth-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local

networks:
  auth-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

This configuration defines services, volumes, networks, healthchecks, and resource limits.

## Volumes for State Persistence

- **pgdata**: Ensures user data survives container restarts. Use named volumes for Docker-managed persistence.
- **redisdata**: Enables Redis AOF persistence for FSM states if needed beyond TTL. Configure RDB snapshots for backups.
- App logs volume for debugging FSM transitions.

Bind mounts for development, named volumes for production.

## Custom Networks

The `auth-network` isolates services, preventing external access except via exposed ports. Services resolve each other by name (e.g., `postgres` hostname).

## Environment Variables for FSM Configurations

Key vars:
- `FSM_STATE_TTL`: Expiration time for idle states (prevents memory leaks).
- `FSM_MAX_CONCURRENT_STATES`: Circuit breaker limit.
- `FSM_TRANSITION_TIMEOUT`: Max time per transition.
- Secrets like `JWT_SECRET`, DB creds (use `.env` or Docker secrets in prod).

Load via `docker-compose --env-file .env up`.

## Scaling

Scale horizontally: `docker-compose up --scale auth-app=3`. Load balance with a reverse proxy like Traefik or Nginx. Redis cluster for state sharding in high-scale setups. Postgres read replicas for queries.

Note: Compose scaling is basic; use Docker Swarm for advanced orchestration.

## Healthchecks for FSM States

Beyond basic connectivity:
- App healthcheck queries `/health/fsm` endpoint, which:
  1. Pings Redis/Postgres.
  2. Counts active FSM instances.
  3. Validates sample state transitions.
  4. Checks for orphaned states (cleanup if > threshold).

Example endpoint logic:
```python
@app.route('/health/fsm')
def fsm_health():
    state_count = redis_client.dbsize()  # Approx FSM states
    if state_count > FSM_MAX_CONCURRENT_STATES:
        return jsonify({'status': 'unhealthy'}), 503
    # Test transition
    return jsonify({'status': 'healthy', 'states': state_count})
```

## Architecture Diagram

```mermaid
graph TB
    Client[Client Requests] -->|HTTP| LoadBalancer[Load Balancer&lt;br/&gt;(Traefik/Nginx)]
    LoadBalancer --> App1[auth-app #1&lt;br/&gt;FSM Logic]
    LoadBalancer --> App2[auth-app #2]
    App1 -->|Queries| Postgres[(postgres&lt;br/&gt;pgdata)]
    App1 -->|States/Sessions| Redis[(redis&lt;br/&gt;redisdata)]
    App2 --> Postgres
    App2 --> Redis
    style Postgres fill:#f9f,stroke:#333
    style Redis fill:#ff9,stroke:#333
```

## Migrating to Production

1. **Secrets Management**: Replace env vars with Docker secrets (`docker secret create`).
2. **Orchestration**: Migrate to Docker Swarm (`docker stack deploy`) or Kubernetes (Helm charts).
3. **Monitoring**: Integrate Prometheus/Grafana for FSM metrics (state transitions/sec, error rates).
4. **CI/CD**: Use GitHub Actions to build/push images, deploy stacks.
5. **Zero-Downtime**: Blue-green deployments via Swarm services.
6. **Backups**: Cron jobs for `pg_dump`, Redis `BGSAVE`.

## Security Best Practices

- **Non-root Containers**: Use `USER 1000` in Dockerfiles.
- **Secrets**: Never hardcode; use Vault or AWS Secrets Manager.
- **Network Policies**: Firewall rules, no public Redis/Postgres exposure.
- **HTTPS/TLS**: Traefik auto-cert with Let's Encrypt.
- **Scanning**: Trivy for vuln scans, `docker scout`.
- **RBAC**: Least privilege DB users (auth-app has INSERT/SELECT only).
- **Rate Limiting**: FSM-integrated throttling per IP/user.
- **Auditing**: Log all state transitions to Postgres.

| Aspect | Best Practice | Tool |
|--------|---------------|------|
| Secrets | Docker Secrets | Vault |
| Scanning | Image vuln check | Trivy |
| Monitoring | Metrics export | Prometheus |
| TLS | Auto certs | Traefik |

This setup ensures a secure, observable, and scalable deployment exceeding 1000 daily active users.

## Conclusion

Docker Compose simplifies local/prod-like deployments for FSM auth services. Start with the provided `docker-compose.yml`, iterate with scaling and monitoring.

**Word count: ~950**