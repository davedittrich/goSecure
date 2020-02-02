SHELL=/bin/bash
TMP:=$(shell psec environments path --tmpdir)
HYPRIOT_VERSION=1.12.0
HYPRIOT_IMG=hypriotos-rpi-v$(HYPRIOT_VERSION).img
HYPRIOT_ZIP=$(HYPRIOT_IMG).zip
HYPRIOT_ZIP_URL=https://github.com/hypriot/image-builder-rpi/releases/download/v$(HYPRIOT_VERSION)/$(HYPRIOT_ZIP)
HYPRIOT_SHA256=$(HYPRIOT_ZIP).sha256
HYPRIOT_SHA256_URL=$(HYPRIOT_ZIP_URL).sha256
CLOUD_CONFIG_CLIENT:=$(TMP)/cloud-config.client
CLOUD_CONFIG_SERVER:=$(TMP)/cloud-config.server
IMAGE=$(HYPRIOT_IMG)

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
	@echo 'hypriot-img - download $(HYPRIOT_ZIP) file, check SHA256 sum, unzip'
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

.PHONY: hypriot-zip
hypriot-zip $(HYPRIOT_ZIP):
	wget -nc $(HYPRIOT_ZIP_URL)
	wget -nc $(HYPRIOT_SHA256_URL)
	sha256sum -c $(HYPRIOT_SHA256)

.PHONY: hypriot-img
hypriot-img $(HYPRIOT_IMG): $(HYPRIOT_ZIP)
	@[ ! -f $(HYPRIOT_IMG) ] && unzip $(HYPRIOT_ZIP) || ls -l $(HYPRIOT_IMG)

.PHONY: client-sd
client-sd:
	@[ -f $(IMAGE) ] || (echo "[-] set IMAGE with path to OS image" && exit 1)
	flash --userdata $(CLOUD_CONFIG_CLIENT) $(IMAGE)

.PHONY: server-sd
server-sd:
	@[ -f $(IMAGE) ] || (echo "[-] set IMAGE with path to OS image" && exit 1)
	flash --userdata $(CLOUD_CONFIG_SERVER) $(IMAGE)

.PHONY: clean
clean:
	[ ! -f "$(CLOUD_CONFIG_CLIENT)" ] || rm "$(CLOUD_CONFIG_CLIENT)"
	[ ! -f "$(CLOUD_CONFIG_SERVER)" ] || rm "$(CLOUD_CONFIG_SERVER)"
	[ ! -f "$(HYPRIOT_IMG)" ] || rm "$(HYPRIOT_IMG)"
	rm -rf goSecure_init/__pycache__
	rm -rf scripts/__pycache__
	rm -rf __pycache__

.PHONY: clean
spotless: clean
	[ ! -f "$(HYPRIOT_ZIP)" ] || rm "$(HYPRIOT_ZIP)"
	[ ! -f "$(HYPRIOT_SHA256)" ] || rm "$(HYPRIOT_SHA256)"

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
