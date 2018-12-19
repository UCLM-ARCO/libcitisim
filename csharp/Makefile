# -*- mode: makefile-gmake; coding: utf-8 -*-

SLICE2CS  ?= slice2cs
SLICE_DIR  = /usr/share/slice
OUT_DIR    = src/generated
SLICES     = iot.ice PropertyService.ice

export DOTNET_SKIP_FIRST_TIME_EXPERIENCE = true
export TEST_DIR = $(shell pwd)/tests

vpath %.ice $(SLICE_DIR)/citisim
vpath %.ice $(SLICE_DIR)/PropertyService
vpath %.cs $(OUT_DIR)


all: $(OUT_DIR) $(SLICES:%.ice=%.cs)

$(OUT_DIR):
	mkdir -p $@

%.cs: %.ice
	$(SLICE2CS) --output-dir $(OUT_DIR) $^

test:
	dotnet test

package:
	dotnet publish -o $$(pwd)/publish src

.PHONY: clean
clean:
	$(RM) -fr $(OUT_DIR)
