.PHONY: all
all: help

.PHONY: help
help:
	@echo 'usage: make target [...]'

.PHONY: clean
clean:
	-rm -f cloud-config.{client,server}

.PHONY: debug-server
debug-server:
	tar -cf - gosecure_app.py forms.py templates/ scripts/ | ssh gosecure sudo tar -C goSecure_Web_GUI/ -xvf -
	ssh gosecure sudo service gosecure restart
