build :
	docker build . -t archiving-composer:latest
run :
	docker run -d archiving-composer:latest 
run-now :
	docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -it archiving-composer:latest ${BODY}
prune :
	docker system prune -f
stop : 
	docker stop archiving-composer
rie :
	docker run --rm -d -v ~/.aws-lambda-rie:/aws-lambda -p 9000:8080 \
    --entrypoint /aws-lambda/aws-lambda-rie \
	--name archiving-composer \
    archiving-composer:latest \
        /usr/local/bin/python -m awslambdaric audiocomposer-local.lambda_handler
push : ecr-tag
	docker push 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer:latest
ecr-tag :
	docker tag archiving-composer:latest 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer:latest
update-lambda : build push
	aws lambda update-function-code \
	--function-name archiving-composer \
	--image-uri 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer:latest \
	--region us-west-2 \
	--publish
authenticate-ecr :
	aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin https://435400990198.dkr.ecr.us-west-2.amazonaws.com