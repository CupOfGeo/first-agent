#!/bin/bash
set -e
REPO_NAME="first-agent"

# dotfile
echo 'alias gs="git status"' >> ~/.zshrc


# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Setup Python environment
uv sync --group dev
uv run pre-commit install


if [ ! -f /workspaces/${REPO_NAME}/.env ]; then
        cp /workspaces/${REPO_NAME}/.env.example /workspaces/${REPO_NAME}/.env
        echo "Created .env file from .env.example"
    else
    echo ".env file already exists, skipping copy"
fi

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install node
npm install -g @anthropic-ai/claude-code

# get inspector and it starts running
# having issues running this inside the dev container idk why
# npx @modelcontextprotocol/inspector
