#!/bin/bash
set -eo pipefail

# Put neovim in the PATH for those who celebrate
mkdir -p ~/.local/bin
ln -s /opt/nvim-linux-x86_64/bin/nvim ~/.local/bin

# Copy tmux configuration
cp /workspaces/claude/.devcontainer/tmux.conf ~/.tmux.conf

# Install Claude Code
# TODO inherit this properly, it's already in devcontainer-on-create
curl -fsSL https://claude.ai/install.sh | bash
echo -e "export CLAUDE_CODE_USE_FOUNDRY=1\nexport ANTHROPIC_FOUNDRY_RESOURCE=uceap-claude-test-resource" | tee -a ~/.bashrc ~/.zshrc ~/.zshrc.local
claude plugin marketplace add UCEAP/claude
claude plugin install uceap

# Set UTF-8 locale for proper character display (tmux prompt special chars)
echo -e "\n# Set UTF-8 locale for proper character display\nexport LANG=en_US.UTF-8\nexport LC_ALL=en_US.UTF-8" | tee -a ~/.bashrc ~/.zshrc ~/.zshrc.local
