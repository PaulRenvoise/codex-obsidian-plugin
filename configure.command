#!/bin/zsh
set -e
cd -- "${0:A:h}"
print 'Obsidian settings are available on the plugin details page.'
print 'You can also enter a vault folder path here.'
read 'VAULT_CHOICE?Vault folder path (blank to show current settings): '
if [[ -n "$VAULT_CHOICE" ]]; then
  python3 ./setup.py --vault "$VAULT_CHOICE"
else
  python3 ./setup.py
fi
read '?Press Enter to close.'
