build :
	sam build
run :
	docker run -d archiving-composer-v3:latest 
run-now :
	docker run -v ${HOME}/.aws/credentials:/root/.aws/credentials:ro -it archiving-composer-v3:latest ${BODY}
prune :
	docker system prune -f
stop : 
	docker stop archiving-composer
rie : 
	docker buildx build -t archiving-composer-v3:latest --file Dockerfile .
	docker run --rm -d -v ~/.aws-lambda-rie:/aws-lambda -p 9000:8080 \
    --entrypoint /aws-lambda/aws-lambda-rie \
	--name archiving-composer-v3 \
    archiving-composer-v3:latest \
        /usr/local/bin/python -m awslambdaric audiocomposer-local.lambda_handler
push : ecr-tag
	docker push 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer-v3:latest
ecr-tag :
	docker tag archiving-composer-v3:latest 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer-v3:latest
update-lambda : build push
	aws lambda update-function-code \
	--function-name archiving-composer-v3 \
	--image-uri 435400990198.dkr.ecr.us-west-2.amazonaws.com/archiving-composer-v3:latest \
	--region us-west-2 \
	--publish
authenticate-ecr :
	aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin https://435400990198.dkr.ecr.us-west-2.amazonaws.com
logs:
	sam logs --stack-name archiving-composer-v3 --tail
deploy : build
	sam deploy
sync: 
	sam sync --stack-name=archiving-composer-v3 --image-repository=435400990198.dkr.ecr.us-west-2.amazonaws.com/archivingcomposerv353d9c6bf/archivingcomposerv3a3aab478repo --watch