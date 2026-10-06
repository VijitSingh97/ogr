# ogr

`ogr` opens a Git repository's remote URL in your browser. Run it from anywhere
inside a worktree, or pass a repository directory.

## Install

With [Homebrew](https://brew.sh/):

```sh
brew tap vijitsingh97/ogr https://github.com/VijitSingh97/ogr.git
brew install vijitsingh97/ogr/ogr
```

If Homebrew reports that the formula is not trusted, run
`brew trust --formula vijitsingh97/ogr/ogr`, then retry the install command.

The formula installs Python 3.13. It uses the system Git on macOS and installs
Git on Linux. macOS uses `/usr/bin/open`; Linux also requires `xdg-open`,
normally provided by the distribution's `xdg-utils` package.

On Ubuntu 22.04 or newer and Debian 12 or newer, use the signed APT repository:

```sh
sudo apt update
sudo apt install ca-certificates curl
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://vijitsingh97.github.io/ogr/ogr.asc \
  | sudo tee /etc/apt/keyrings/ogr.asc >/dev/null
sudo tee /etc/apt/sources.list.d/ogr.sources >/dev/null <<'EOF'
Types: deb
URIs: https://vijitsingh97.github.io/ogr/
Suites: ./
Signed-By: /etc/apt/keyrings/ogr.asc
EOF
sudo apt update
sudo apt install ogr
```

The signing key fingerprint is
`0CC3 C39C A957 4C9B 1F52 C2E8 A8EB 1080 B99F F3C0`. The key is scoped to this
repository by `Signed-By`. The architecture-independent package requires Python
3.9 or newer and installs Git and `xdg-utils` through APT.

If you previously defined `ogr` as a Zsh function, that function shadows the
installed command. Remove its definition from `.zshrc`, then restart the shell,
or run `unfunction ogr` for the current session.

## Usage

Run `ogr [options] [directory]`. The directory defaults to the current one.

- `-b, --branch` opens the current branch on GitHub, GitLab, or Bitbucket.
- `-r NAME, --remote NAME` selects a remote; the default is `origin`.
- `-p, --print` prints the URL without opening a browser.
- `-h, --help` shows help, and `-V, --version` shows the version.

Examples:

```sh
ogr
ogr -b
ogr --remote upstream ~/src/project
ogr --print .
```

Without `--branch`, `ogr` opens the repository root for any HTTP(S), SSH,
scp-style, or `git://` remote. It preserves HTTP(S) and converts SSH and `git://`
remotes to HTTPS, removes a trailing `.git`, credentials, query, fragment, and
SSH port, and retains an
explicit HTTP(S) port. Spaces and Unicode characters are percent-encoded.

Branch pages are supported on:

- github.com: `/tree/<branch>`
- gitlab.com: `/-/tree/<branch>`
- bitbucket.org: `/src/<branch>`

Branch names are percent-encoded, including `/`, for GitHub and GitLab.
Bitbucket branch links do not support names containing `/`, so `ogr` rejects
those names. Other hosts can open the repository root but return a clear error
for `--branch` because their branch URL formats vary. A detached `HEAD` also
returns an error. An unborn branch works when Git can resolve its symbolic
branch name.

Use `--print` in scripts or to inspect the normalized URL without starting a
browser.

## Shell completion

Both packages install Bash and Zsh completions for options, remote names, and
repository directories. Open a new terminal after installation.

For Bash, add the line matching your installation to `~/.bashrc`:

```sh
source "$(brew --prefix)/etc/bash_completion.d/ogr"       # Homebrew
# source /usr/share/bash-completion/completions/ogr      # APT
# source "$HOME/.local/share/bash-completion/completions/ogr" # Source
```

For Zsh, add the appropriate directory to `fpath` before your existing
`compinit` call, or before loading Oh My Zsh:

```sh
fpath=("$(brew --prefix)/share/zsh/site-functions" $fpath) # Homebrew
# fpath=(/usr/share/zsh/vendor-completions $fpath)        # APT
# fpath=("$HOME/.local/share/zsh/site-functions" $fpath)  # Source
```

If completion is not enabled yet, add `autoload -Uz compinit; compinit` after
that line. Oh My Zsh already runs `compinit`.

## Development

```sh
make test check
make install PREFIX="$HOME/.local"
```

`make install` supports `PREFIX` and `DESTDIR` staging and installs Bash and Zsh
completions with the command.

Licensed under the [MIT License](LICENSE).
