build :
	docker build . -t archiving-composer:latest --no-cache
run :
	docker run -d archiving-composer:latest 
run-now :
	docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -it archiving-composer:latest ${BODY}
prune :
	docker system prune -f
push : ecr-tag
	docker push 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer:latest
ecr-tag :
	docker tag archiving-composer:latest 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer:latest