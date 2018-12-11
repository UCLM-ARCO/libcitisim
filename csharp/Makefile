
export DOTNET_SKIP_FIRST_TIME_EXPERIENCE = true
export TEST_DIR = $(shell pwd)/tests

all:
	mkdir -p src/generated
	slice2cs --output-dir src/generated /usr/share/slice/citisim/iot.ice

test:
	dotnet test
