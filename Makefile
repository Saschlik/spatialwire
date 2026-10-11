PREFIX ?= /usr/local
BINDIR ?= $(PREFIX)/bin
DATADIR ?= $(PREFIX)/share
APPDIR ?= $(DATADIR)/applications
PRESETSDIR ?= $(DATADIR)/spatialwire/presets
ASSETSDIR ?= $(DATADIR)/spatialwire/assets

.PHONY: all install uninstall clean

all:
	@echo "SpatialWire is ready to install. Run 'sudo make install'."

install:
	install -Dm755 bin/spatialwire $(DESTDIR)$(BINDIR)/spatialwire
	install -Dm755 ui/spatialwire_gui.py $(DESTDIR)$(BINDIR)/spatialwire-settings
	install -Dm644 ui/com.github.saschlik.SpatialWire.desktop $(DESTDIR)$(APPDIR)/com.github.saschlik.SpatialWire.desktop
	mkdir -p $(DESTDIR)$(DATADIR)/spatialwire/src
	cp -r src/* $(DESTDIR)$(DATADIR)/spatialwire/src/
	mkdir -p $(DESTDIR)$(PRESETSDIR)
	cp -r presets/* $(DESTDIR)$(PRESETSDIR)/
	mkdir -p $(DESTDIR)$(ASSETSDIR)
	cp -r assets/* $(DESTDIR)$(ASSETSDIR)/

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/spatialwire
	rm -f $(DESTDIR)$(BINDIR)/spatialwire-settings
	rm -f $(DESTDIR)$(APPDIR)/com.github.saschlik.SpatialWire.desktop
	rm -rf $(DESTDIR)$(DATADIR)/spatialwire

clean:
	rm -rf __pycache__ src/__pycache__ ui/__pycache__
