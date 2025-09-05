# run only on a new project
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

uv init
uv add --group dev pre-commit
