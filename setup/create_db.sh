#!/bin/bash

# Define and export environment variables
export DB_NAME="MLOps-db"
export DB_USER="MLOps-user"
export DB_PASSWORD=$(openssl rand -hex 12)         # Random 24-character hex password
export DB_ADMIN_PASSWORD=$(openssl rand -hex 12)   # Random 24-character hex password

# Add Helm repo
helm repo add databases https://inseefrlab.github.io/helm-charts-databases

# Create values.yaml from template
cat << EOF > ./values.yaml
postgresql:
  image:
    tag: "16"
  primary:
    persistence:
      enabled: true
      size: 10Gi
    resources:
      requests:
        cpu: 250m
        memory: 1Gi
      limits:
        cpu: 30000m
        memory: 50Gi
  auth:
    postgresPassword: ${DB_ADMIN_PASSWORD}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}
  extensions:
    postgis: false
security:
  networkPolicy:
    enabled: true
    from:
      - ipBlock:
          cidr: 10.233.103.0/32
      - ipBlock:
          cidr: 10.233.111.0/32
      - ipBlock:
          cidr: 10.233.116.0/32
      - ipBlock:
          cidr: 10.233.108.0/32
discovery:
  enabled: true
userPreferences:
  language: fr
EOF

# Try to create databases with different ids in case the first is not available
max_attempts=5
attempt=1

while [ $attempt -le $max_attempts ]; do
    export DB_HOST="postgresql-$(shuf -i 100000-999999 -n 1)"  # Random 6-digit number

    echo "Attempt $attempt: Trying DB_HOST=${DB_HOST}..."

    if helm install "${DB_HOST}" databases/postgresql -f; then
        echo "✅ PostgreSQL installed successfully at ${DB_HOST}"
        break
    else
        echo "❌ Helm install failed at ${DB_HOST}."
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ All ${max_attempts} attempts failed. Exiting."
    exit 1
fi
