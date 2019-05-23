# -*- mode: makefile-gmake; coding: utf-8 -*-
DESTDIR ?= ~

SRC      = build/lib/libcitisim

PY2DIST  = /usr/lib/python2.7/dist-packages/libcitisim
PY3DIST  = /usr/lib/python3/dist-packages/libcitisim
DOCDIR   = $(DESTDIR)/usr/share/doc

CITISIM_DIR      ?= ../prj.citisim
WIRING_SRV_DIR   ?= ../citisim-wiring-server/
PROPERTY_SRV_DIR ?= ../ice.property-service-simple/
ENERGY_MODEL_DIR ?= ../citisim-energymodel/

all:
	python3 setup.py bdist

source:
	$(RM) -r slice
	mkdir -p slice/citisim
	mkdir -p slice/PropertyService
	cp $(CITISIM_DIR)/slice/*.ice slice/citisim
	cp $(WIRING_SRV_DIR)/src/*.ice slice/citisim
	cp $(PROPERTY_SRV_DIR)/src/*.ice slice/PropertyService
	cp $(ENERGY_MODEL_DIR)/energy.ice slice/citisim
	python3 setup.py sdist

tests:
	nosetests3 test/test_*.py

install-depends:
	sudo apt install \
		python3-nose \
		python3-doublex \
		python3-zeroc-ice \
		citisim-slice \
		zeroc-ice37 \
 		zeroc-ice37-services \
		zeroc-icebox \
		property-service-simple

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
	$(RM) -r slice dist libcitisim.egg-info build *.retry
