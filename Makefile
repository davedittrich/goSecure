debug-server:
	tar -cf - gosecure_app.py forms.py templates/ scripts/ | ssh gosecure sudo tar -C goSecure_Web_GUI/ -xvf -
	ssh gosecure sudo service gosecure restart
