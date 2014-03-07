prefix=/usr/local

install:
	install -m 0755 argusarchive $(prefix)/bin
	install -m 0644 bargus_functions.sh $(prefix)/bin
	install -m 0644 cargus_functions.sh $(prefix)/bin
	install -m 0755 barguspy $(prefix)/bin
	install -m 0755 bargus $(prefix)/bin
	install -m 0755 cargus $(prefix)/bin
	cp argus-server /etc/init.d/
	cp argus.conf /etc/argus.conf

.PHONY: install
