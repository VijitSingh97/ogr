PREFIX ?= $(HOME)/.local
DESTDIR ?=
PYTHON ?= python3
ZSH_COMPLETION_DIR ?= $(PREFIX)/share/zsh/site-functions

.PHONY: install test check deb

install:
	install -d "$(DESTDIR)$(PREFIX)/bin"
	install -m 755 bin/ogr "$(DESTDIR)$(PREFIX)/bin/ogr"
	install -d "$(DESTDIR)$(PREFIX)/share/bash-completion/completions"
	install -m 644 completions/ogr.bash "$(DESTDIR)$(PREFIX)/share/bash-completion/completions/ogr"
	install -d "$(DESTDIR)$(ZSH_COMPLETION_DIR)"
	install -m 644 completions/_ogr "$(DESTDIR)$(ZSH_COMPLETION_DIR)/_ogr"

test:
	PYTHONDONTWRITEBYTECODE=1 $(PYTHON) -m unittest discover -s tests

check:
	$(PYTHON) -c "compile(open('bin/ogr', encoding='utf-8').read(), 'bin/ogr', 'exec')"

deb:
	./scripts/build-deb.sh
