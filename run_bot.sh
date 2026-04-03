#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

cd /home/iver/.openclaw/agents/cody/workspace/projects/sigma

if [ -f private.env ]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and lines that are purely comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Remove inline comments: everything after the first unescaped '#'
        line_no_comment="${line%%\#*}"
        # Remove trailing whitespace from the line
        line_no_comment="${line_no_comment%"${line_no_comment##*[![:space:]]}"}"

        # Parse key=value
        if [[ "$line_no_comment" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            
            # Remove leading/trailing quotes if present
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            
            # Export the variable
            export "$key=$value"
        fi
    done < private.env
fi

# Check required variables (optional, but good practice)
if [ -z "$PRIVATE_KEY" ] || [ -z "$FLASHBOTS_KEY" ]; then
    echo "Error: PRIVATE_KEY or FLASHBOTS_KEY is not set. Please check your private.env file." >&2
    exit 1
fi

# Run the bot with pipenv and redirect logs
# Using 'nohup' and '&' to keep the process running in the background
# Redirecting stdout and stderr to sigma.log
nohup pipenv run python main.py >> logs/sigma.log 2>&1 &
