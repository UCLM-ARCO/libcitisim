export DOTNET_SKIP_FIRST_TIME_EXPERIENCE = true

all:

install-deps:
	@mkdir -p nugets
	@wget -rqnH --cut-dirs=3 --no-parent -P nugets http://arco.esi.uclm.es/public/nugets/

run-publisher:
	dotnet run

.PHONY: clean vclean
clean:
	$(RM) -fr obj bin

vclean: clean
	$(RM) -rf nugets
