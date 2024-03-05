# Archiving Composer #

Based on <https://github.com/opentok/archiving-composer>

This code is heavily modified and customized by StoryCorps for StoryCorps Connect and StoryCorps Virtual

## Background ##

This script takes an Archive Event JSON packet from Vonage's API (or our internal tools) and does the following

* Downloads the audio archive from S3 where Vonage has stored it, unizps it
* Takes the individual track files and converts them to WAV
* Combines ALL the WAV files into one mixed WAV
* Uploads this to the appropriate "processed" folder on S3.

This had previously been run as a flask-based Lambda process. It is now being moved into a containerized process in the hopes of being able to speed up the overall processing time and reducing failed processing events.

The Lambda function can be found on AWS here: <https://us-west-2.console.aws.amazon.com/lambda/home?region=us-west-2#/functions/archiving-composer>

## A note on python dependencies ##

Currently any python you need will also need to be specified in the Dockerfile. This is not ideal and will be addressed in the future.

For local development work, we use pipenv to manage dependencies.

## Local Dev ##

*The content below is outdated as of 3/5/24. It will be updated soon.*

There are different ways to work with the local code while doing testing. Option 1 (docker) is the closest to production so it's advisable to try this out at least once before deploying to production. Option 2 is a bit easier to work with but is not as close to production.

### Option 1: Docker ###

To work with the below, you'll need the AWS CLI, Python 3.8+ and possibly a few other things I'm forgetting.

The code for this process is all in `audiocomposer-local.py`. The other versions are present for historical reference.

* Rename `credentials.json.sample` to `credentials.json` and enter your AWS credentials for testing.
* To build the container locally, run `make build`
* `make rie` will let you test locally using AWS's Runtime Interface Emulator ( see <https://docs.aws.amazon.com/lambda/latest/dg/images-test.html> and example curl request below)
* In order to use RIE, you'll need to confirm that the RIE server is installed on your local machine. [installation instructions](https://github.com/aws/aws-lambda-python-runtime-interface-client/tree/main#local-testing).

#### Local dev curl request example ####

```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"id":"969c848c-ab7f-4422-9ca4-87c89679e17d","status":"uploaded","name":"prd000979::Jo::8/11/2022::6:06:10 PM","reason":"user initiated","sessionId":"2_MX40NjU2NTU1Mn5-MTY2MDA3MDk2MTA5M35Sb2sva3BHbUF5VkFxNTZUcEk2ejFxaXd-fg","applicationId":"46565552","createdAt":1660241171000,"size":50288301,"duration":295,"outputMode":"individual","streamMode":"auto","hasAudio":true,"hasVideo":true,"sha256sum":"FfqrOb5ohj6Vahst4ixBxsoCT1WRWkXVJaenwcjNXw0=","password":"","updatedAt":1660241500000,"multiArchiveTag":"","event":"archive","partnerId":46565552,"projectId":46565552,"url":null}'
```

Current package setup based on: <https://pypi.org/project/awslambdaric/>

### Option 2: Local Python ###

* Rename `credentials.json.sample` to `credentials.json` and enter your AWS credentials for testing.
* `pipenv install` to install the dependencies
* `pipenv run python audiocomposer-local.py --event='[THE JSON EVENT FROM VONAGE]'`
* You can also pass in a json file with the `--file` flag

## Deploying ##

* `make deploy` will build, tag and deploy the container to AWS's ECR registry and update the Lambda function with the latest.

## Example vonage payload ##

```json

{
  "id": "7dff3caa-4b49-40c0-8ed0-9c63215129db",
  "status": "uploaded",
  "name": "prd000775-new::S::2020-5-12::00:58:44",
  "reason": "user initiated",
  "sessionId": "2_MX40NjU2NTU1Mn5-MTU4OTI0NTEwOTQzOX4yVk9PRzZvMS9Kd0Q2ZjcxanB4UFBpTmR-fg",
  "projectId": 46565552,
  "createdAt": 1589245124000,
  "size": 61903,
  "duration": 15,
  "outputMode": "individual",
  "hasAudio": true,
  "hasVideo": true,
  "certificate": "",
  "sha256sum": "81318e05-7f56-4d4d-90fc-8b59b7228b4a",
  "password": "",
  "updatedAt": 1589245144053,
  "width": -1,
  "height": -1,
  "partnerId": 46565552,
  "event": "archive"
}

```

* The first three pieces are the important ones -
  * id (archive id) tells the script where to find the .zip that contains the webms and json file;
  * status - non upload status is ignored;
  * name - this text is split on :: and the first segment is used to name the files.
