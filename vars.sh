# The full url to your hipchat server
export HIPCHAT_URL="https://hipchat...../"

# The numeric room ID for the room to notify in.
export ROOM_ID=1 

# The API Token for Hipchat
export TOKEN="..."

# Config for the helper scripts

# Name of the ZIP to create
ZIP_NAME="newrelic-hipchat-lambda.zip"

# Python source file, likely not need changing
PYTHON_SOURCE="newrelic-hipchat-lambda.py"

# Virtual env dir, used to pull out deps.
VIRTUAL_ENV_DIR="venv"

# AWS profile (from ~/.aws/config) to use for upload
AWS_PROFILE="....."

# Default AWS region
REGION="eu-west-1"
