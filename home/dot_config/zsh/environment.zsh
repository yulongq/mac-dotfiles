eval "$(env -u HOMEBREW_BREW_FILE -u HOMEBREW_PATH /opt/homebrew/bin/brew shellenv)"
typeset -U path fpath

export EDITOR=nvim
export GIT_EDITOR=nvim
export BUNDLER_EDITOR=nvim
export MANPAGER='less -X'
export HOMEBREW_CASK_OPTS='--appdir=/Applications'
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"
export RIPGREP_CONFIG_PATH="$HOME/.ripgreprc"
export STARSHIP_CONFIG="$HOME/.config/starship.toml"
export SOURCE_ANNOTATION_DIRECTORIES=spec
export RUBY_CONFIGURE_OPTS="--with-opt-dir=/opt/homebrew/opt/openssl:/opt/homebrew/opt/readline:/opt/homebrew/opt/libyaml:/opt/homebrew/opt/gdbm"
export PKG_CONFIG_PATH=/opt/homebrew/opt/libpq/lib/pkgconfig
export GPG_TTY="$TTY"
export SSH_AUTH_SOCK="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
export PKB_PATH="$HOME/personal-knowledge-base"
export SURGE_HOME="$HOME/Library/Mobile Documents/iCloud~com~nssurge~inc/Documents"
alias SURGE_HOME='cd "$SURGE_HOME"'
export FZF_DEFAULT_COMMAND='rg --files --hidden --follow --no-ignore-vcs'
export FZF_DEFAULT_OPTS='--height 75% --layout=reverse --border'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
export FZF_ALT_C_COMMAND='fd --type d . --color=never'
export https_proxy=http://127.0.0.1:6152
export http_proxy=http://127.0.0.1:6152
export all_proxy=socks5://127.0.0.1:6153

# OrbStack contributes completion paths before the interactive shell runs compinit.
[[ ! -r "$HOME/.orbstack/shell/init.zsh" ]] || source "$HOME/.orbstack/shell/init.zsh"
