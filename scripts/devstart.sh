#!/bin/bash
set -e
REPO_NAME="first-agent"

# dotfile
echo 'alias gs="git status"' >> ~/.zshrc

# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt update
apt install gh -y
sudo apt install sqlite3

# Install SELinux development tools
sudo apt-get install -y \
    selinux-utils \
    selinux-policy-dev \
    policycoreutils \
    checkpolicy \
    semodule-utils

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Setup Python environment
uv sync --group dev
uv run pre-commit install

# move .env.example to .env if .env does not exist
if [ ! -f /workspaces/${REPO_NAME}/.env ]; then
        cp /workspaces/${REPO_NAME}/.env.example /workspaces/${REPO_NAME}/.env
        echo "Created .env file from .env.example"
    else
    echo ".env file already exists, skipping copy"
fi

# Claude Code install
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="/usr/local/share/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
nvm install node
npm install -g @anthropic-ai/claude-code
