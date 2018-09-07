SHELL=/bin/bash
TMP:=$(shell psec environments path --tmpdir)
IMAGE=hypriotos-rpi-v1.7.1.img.zip
CLOUD_CONFIG_CLIENT:=$(TMP)/cloud-config.client
CLOUD_CONFIG_SERVER:=$(TMP)/cloud-config.server

.PHONY: all
all: help

.PHONY: help
help:
	@echo 'usage: make target [...]'
	@echo ''
	@echo 'TARGETS:'
	@echo 'cloud-configs - generate cloud-config files from template "cloud-config.j2"'
	@echo 'client-sd - create SD card for goSecure client'
	@echo 'server-sd - create SD card for goSecure server'
	@echo 'clean - delete temporary files'
	@echo ''
	@echo 'DEVELOPMENT/DEBUGGING TARGETS:'
	@echo 'variables - show variables'
	@echo 'debug-server - copies current code to server and restarts service'
	@echo ''
	@echo 'To generate new secrets, run "psec secrets generate"'
	@echo 'To set undefined string secrets, run "psec secrets set --undefined"'

.PHONY: cloud-configs
cloud-configs: $(CLOUD_CONFIG_CLIENT) $(CLOUD_CONFIG_SERVER)

$(CLOUD_CONFIG_CLIENT): cloud-config.client.j2
	@[ -d $(TMP) ] || (echo "TMP does not point to a valid directory" && exit 1)
	psec template $< $@

$(CLOUD_CONFIG_SERVER): cloud-config.server.j2
	@[ -d $(TMP) ] || (echo "TMP does not point to a valid directory" && exit 1)
	psec template $< $@

.PHONY: client-sd
client-sd:
	[ -f $(IMAGE) ] || (echo "set IMAGE with path to OS image" && exit 1)
	flash --userdata $(CLOUD_CONFIG_CLIENT) $(IMAGE)

.PHONY: server-sd
server-sd:
	[ -f $(IMAGE) ] || (echo "set IMAGE with path to OS image" && exit 1)
	flash --userdata $(CLOUD_CONFIG_SERVER) $(IMAGE)

.PHONY: clean
clean:
	[ ! -f "$(CLOUD_CONFIG_CLIENT)" ] || rm "$(CLOUD_CONFIG_CLIENT)"
	[ ! -f "$(CLOUD_CONFIG_SERVER)" ] || rm "$(CLOUD_CONFIG_SERVER)"

.PHONY: variables
variables: Makefile
	@echo TMP="$(TMP)"
	@echo CLOUD_CONFIG_CLIENT="$(CLOUD_CONFIG_CLIENT)"
	@echo CLOUD_CONFIG_SERVER="$(CLOUD_CONFIG_SERVER)"
	@echo \$\@=$@
	@echo \$\<=$<


.PHONY: debug-server
debug-server:
	tar -cf - gosecure_app.py forms.py templates/ scripts/ | ssh gosecure sudo tar -C goSecure_Web_GUI/ -xvf -
	ssh gosecure sudo service gosecure restart
