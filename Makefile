build :
	docker build . -t archiving-composer:latest --no-cache
run :
	docker run -d archiving-composer:latest 
run-now :
	docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -it archiving-composer:latest ${BODY}
prune :
	docker system prune -f