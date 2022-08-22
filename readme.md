# Archiving Composer # 

Based on https://github.com/opentok/archiving-composer

This code is heavily modified and customized by StoryCorps for StoryCorps Connect and StoryCorps Virtual
## Background ##    
This script takes an Archive Event JSON packet from Vonage's API (or our internal tools) and does the following

* Downloads the audio archive from S3 where Vonage has stored it, unizps it
* Takes the individual track files and converts them to WAV
* Combines ALL the WAV files into one mixed WAV
* Uploads this to the appropriate "processed" folder on S3.

This had previously been run as a flask-based Lambda process. It is now being moved into a containerized process in the hopes of being able to speed up the overall processing time and reducing failed processing events.

The Lambda function can be found on AWS here: https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/functions/archiving-composer
# Local Dev #

To work with the below, you'll need the AWS CLI, Python 3.8+ and possibly a few other things I'm forgetting.

The code for this process is all in `audiocomposer-local.py`. The other versions are present for historical reference.

* Rename `credentials.json.sample` to `credentials.json` and enter your AWS credentials for testing.
* To build the container locally, run `make build`
* `make rie` will let you test locally using AWS's Runtime Interface Emulator ( see https://docs.aws.amazon.com/lambda/latest/dg/images-test.html and example curl request below)
* `make push` will build, tag and deploy the container to AWS's ECR registry and update the Lambda function with the latest.
* If this command says that you are not authenticated, use `make authenticate-ecr`

## Local dev curl request example ##
```
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"id":"969c848c-ab7f-4422-9ca4-87c89679e17d","status":"uploaded","name":"prd000979::Jo::8/11/2022::6:06:10 PM","reason":"user initiated","sessionId":"2_MX40NjU2NTU1Mn5-MTY2MDA3MDk2MTA5M35Sb2sva3BHbUF5VkFxNTZUcEk2ejFxaXd-fg","applicationId":"46565552","createdAt":1660241171000,"size":50288301,"duration":295,"outputMode":"individual","streamMode":"auto","hasAudio":true,"hasVideo":true,"sha256sum":"FfqrOb5ohj6Vahst4ixBxsoCT1WRWkXVJaenwcjNXw0=","password":"","updatedAt":1660241500000,"multiArchiveTag":"","event":"archive","partnerId":46565552,"projectId":46565552,"url":null}'
```


Current package setup based on: https://pypi.org/project/awslambdaric/
