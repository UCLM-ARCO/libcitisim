# -*- mode: makefile-gmake; coding: utf-8 -*-

VER       ?= $(shell date +%Y.%m%d)
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
	zip -r libcitisim-cs-$(VER).zip publish/*.dll -x publish/Microsoft.CSharp.dll

.PHONY: clean vclean
clean:
	$(RM) -r *.zip publish

vclean: clean
	$(RM) -r $(OUT_DIR)
