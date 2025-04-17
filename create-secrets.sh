#!/bin/bash

# Script to generate a Kubernetes Secret from environment variables.
# These environment variables are expected to be set in your current shell.
# This script will create a generic secret named "app-credentials".

# Define the name of the Kubernetes Secret
SECRET_NAME="movie-reviews-tracker-credentials"

# Array of key-value pairs for the secret.
# The key will be the name in the secret, and the value will be
# sourced from the corresponding environment variable.
declare -A CREDENTIALS=(
  ["DB_NAME"]="${DB_NAME}"
  ["DB_USER"]="${DB_USER}"
  ["DB_PASSWORD"]="${DB_PASSWORD}"
  ["DB_HOST"]="${DB_HOST}"
  ["OPENAI_API_KEY"]="${OPENAI_API_KEY}"
  ["AWS_ACCESS_KEY_ID"]="${AWS_ACCESS_KEY_ID}"
  ["AWS_SECRET_ACCESS_KEY"]="${AWS_SECRET_ACCESS_KEY}"
  ["AWS_SESSION_TOKEN"]="${AWS_SESSION_TOKEN}"
  ["AWS_S3_ENDPOINT"]="${AWS_S3_ENDPOINT}"
  ["AWS_DEFAULT_REGION"]="${AWS_DEFAULT_REGION}"
)

# Check if all required environment variables are set
missing_vars=()
for key in "${!CREDENTIALS[@]}"; do
  if [ -z "${CREDENTIALS[$key]}" ]; then
    missing_vars+=("$key")
  fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
  echo "Error: The following environment variables are not set:"
  for var in "${missing_vars[@]}"; do
    echo "- ${var}"
  done
  echo "Please set these variables before running this script."
  exit 1
fi

# Construct the kubectl create secret command
kubectl_command="kubectl create secret generic $SECRET_NAME"

# Add each credential as a --from-literal argument
for key in "${!CREDENTIALS[@]}"; do
  kubectl_command+=" --from-literal=$key=\"${CREDENTIALS[$key]}\""
done

# Execute the kubectl command
echo "Creating Kubernetes Secret: $SECRET_NAME"
eval "$kubectl_command"

echo "Kubernetes Secret '$SECRET_NAME' created successfully."