export DOTNET_SKIP_FIRST_TIME_EXPERIENCE = true

all:

install-deps:
	@mkdir -p nugets
	@echo "-> Please, download 'libcitisim.xx.nupkg' from bitbucket"
	@echo "-> and copy it inside 'nugets' folder"
	@echo "-> URL: https://bitbucket.org/arco_group/libcitisim/downloads/"

run-publisher:
	dotnet run

.PHONY: clean vclean
clean:
	$(RM) -fr obj bin

vclean: clean
	$(RM) -rf nugets
