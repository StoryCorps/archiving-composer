build :
	docker build . -t archiving-composer:latest --no-cache
run :
	docker run -d archiving-composer:latest 
run-now :
	docker run -v ${HOME}/.aws/credentials:/home/appuser/.aws/credentials:ro -it archiving-composer:latest 