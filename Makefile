# -*- mode: makefile-gmake; coding: utf-8 -*-
DESTDIR ?= ~

SRC      = build/lib/libcitisim

PY2DIST  = /usr/lib/python2.7/dist-packages/libcitisim
PY3DIST  = /usr/lib/python3/dist-packages/libcitisim
DOCDIR   = $(DESTDIR)/usr/share/doc

CITISIM_DIR = ../prj.citisim

all:
	python3 setup.py bdist

source:
	$(RM) -r slice; mkdir -p slice/citisim; cp $(CITISIM_DIR)/slice/*.ice slice/citisim
	python3 setup.py sdist

tests:
	nosetests3 test/*.py

vagrant-ice36-tests:
	@if vagrant status ice36 | grep "^ice36" | grep -v running; then \
	    vagrant up ice36; \
	fi
	vagrant ssh ice36 -c "cd /vagrant; make tests"

vagrant-ice37-tests:
	@if vagrant status ice37 | grep "^ice37" | grep -v running; then \
	    vagrant up ice37; \
	fi
	vagrant ssh ice37 -c "cd /vagrant; make tests"

install:
	install -vd $(DESTDIR)$(PY2DIST)
	install -v -m 444 $(SRC)/* $(DESTDIR)$(PY2DIST)
	install -vd $(DESTDIR)$(PY3DIST)
	install -v -m 444 $(SRC)/* $(DESTDIR)$(PY3DIST)


.PHONY: clean
clean:
	$(RM) -r slice dist libcitisim.egg-info build
