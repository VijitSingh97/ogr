#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
version=$(cat VERSION)
SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-$(git log -1 --format=%ct)}
export SOURCE_DATE_EPOCH
package=$(mktemp -d)
trap 'rm -rf "$package"' EXIT
make install DESTDIR="$package" PREFIX=/usr ZSH_COMPLETION_DIR=/usr/share/zsh/vendor-completions
install -d "$package/DEBIAN" "$package/usr/share/doc/ogr"
install -m 644 LICENSE "$package/usr/share/doc/ogr/copyright"
cat > "$package/DEBIAN/control" <<CONTROL
Package: ogr
Version: $version
Section: utils
Priority: optional
Architecture: all
Maintainer: Vijit Singh <VijitSingh97@users.noreply.github.com>
Depends: python3 (>= 3.9), git, xdg-utils
Homepage: https://github.com/VijitSingh97/ogr
Description: Open a Git repository's remote in your browser
 Opens repository or branch URLs, or prints them for headless use.
 Includes Bash and Zsh completion.
CONTROL
mkdir -p dist
dpkg-deb --root-owner-group --build "$package" "dist/ogr_${version}_all.deb"
