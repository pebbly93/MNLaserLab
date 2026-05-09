#!/bin/zsh
cd "$(dirname "$0")"
if [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
export PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/bin:$PATH"
npm install
/opt/homebrew/opt/node@20/bin/node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 || npm run dev
