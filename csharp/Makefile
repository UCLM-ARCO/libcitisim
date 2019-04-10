# -*- mode: makefile-gmake; coding: utf-8 -*-

DOTNETURL  = https://dotnet.microsoft.com/download/linux-package-manager/debian9/sdk-current
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

test-this: F ?= ""
test-this:
	dotnet test --filter "$(F)"

package:
	dotnet publish -o $$(pwd)/LibCitisim src
	zip -r libcitisim-cs-$(VER).zip LibCitisim/*.dll -x LibCitisim/Microsoft.CSharp.dll

install-deps:
	@echo "Please, visit $(DOTNETURL) for more information about installing .NET SDK"

.PHONY: clean vclean
clean:
	$(RM) -r *.zip LibCitisim

vclean: clean
	$(RM) -r $(OUT_DIR)
