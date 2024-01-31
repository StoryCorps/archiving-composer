from __future__ import print_function
from multiprocessing import Value

import urllib
import urllib3
import zipfile
import boto3
import io
import os
import json
import subprocess
import re
import time
import shutil
from datetime import datetime
from dateutil.parser import parse
import sys
import pprint
import csv
import requests
import zipfile
import shlex
import argparse
import json
from icecream import ic

# add sentry
import sentry_sdk
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

sentry_sdk.init(
    dsn="https://02c59fc0622254ae590c302fe4ca7f36@o1088143.ingest.sentry.io/4506667625349120",
    integrations=[AwsLambdaIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)

def lambda_handler(event, context):
    tmp = '/tmp/'

    # exit if there's no event provided
    if not event:
        ic('No JSON provided.')
        return

    # if event is a string, parse it from json
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event

    # # Cover cases where the lambda is being called directly OR it's being called through the API Gateway
    # if 'body' in event:
    #     body = event['body']
    # else:
    #     body = event

    bucket = "storycorps-signature-remote"
    account = str(body["partnerId"])
    interview = str(body["id"])
    interviewId = str(re.split('::', body["name"])[0]).lower().replace(" ", "")
    status = body["status"]
    http = urllib3.PoolManager()
    jsonData = {}
    jsonData["venue"] = interviewId[0:3]
    jsonData["Interview ID"] = interviewId
    jsonData["Archive ID"] = interview

    if (status != "uploaded"):
        ic(interviewId, "not an upload event.", status)
        resp = json.dumps(success=True)
        resp.status_code = 200
        return resp

    # load credentials json file
    with open('credentials.json') as json_file:
        data = json.load(json_file)
        access_key = data["aws_access_key_id"]
        secret_key = data["aws_secret_access_key"]

    s3_client = boto3.client(
        's3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    s3_resource = boto3.resource(
        's3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    my_bucket = s3_resource.Bucket(bucket)

    zippedKey = account + "/" + interview + "/archive.zip"
    unzippedLocation = account + "/" + interview
    temp_dir = tmp + interview
    interviewId = interviewId.lower()

    webmURLDict = {}

    try:
        key = zippedKey
        print(interviewId, "unzipping", bucket, key)
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        putObjects = []
        with io.BytesIO(obj["Body"].read()) as tf:
            # Read the file as a zipfile and process the members
            with zipfile.ZipFile(tf, mode='r') as zipf:
                for file in zipf.infolist():
                    fileName = account + "/" + interview + "/" + file.filename
                    putFile = s3_client.put_object(
                        Bucket=bucket, Key=fileName, Body=zipf.read(file))
                    putObjects.append(putFile)

        # for each object in the bucket/account/archiveID directory
        objs = my_bucket.objects.filter(Prefix=unzippedLocation)

        # make a folder in tmp
        print(
            interviewId, "creating folder, generating presigned webm URLs", tmp + interview)
        if not os.path.exists(tmp + interview):
            # os.mkdir(tmp + interview, 0777)
            os.mkdir(tmp + interview)

        # download the json and generate signed URLs for the wembs.
        for obj in objs:
            if (obj._key[-5:] == ".json"):
                s3_client.download_file(
                    bucket, obj.key, tmp + interview + "/interview.json")
            elif (obj._key[-5:] == ".webm"):
                webmURLDict[obj.key[-41:]] = "\"" + s3_client.generate_presigned_url(
                    'get_object', Params={'Bucket': bucket, 'Key': obj._key}, ExpiresIn=1000000) + "\""
            pass

        # open the JSON file
        f = open(tmp + interview + '/interview.json',)

        # returns JSON object as a dictionary
        data = json.load(f)
        startTime = 10000000000000
        endTime = 0

        # delete the files that are empty (size < 600)
        print(interviewId, "calculating time offsets")
        count = 0
        while count < len(data['files']):
            if (data['files'][count]["size"] < 600):
                del data['files'][count]
                print(interviewId, "found empty file - excluding from processing")
            else:
                count = count + 1

        # find start end end time for the whole playback
        for file in data['files']:
            if (file["startTimeOffset"] < startTime):
                startTime = file["startTimeOffset"]
            if (file["stopTimeOffset"] > endTime):
                endTime = file["stopTimeOffset"]

        for file in data['files']:
            file["startTimeOffset"] -= startTime
            file["stopTimeOffset"] -= endTime

        inputs = ""
        streamCount = 1
        individualStreams = []

        print(interviewId, "processing individual streams")

        for file in data['files']:
            ic(file["connectionData"])
            try:
                # generate a single wavefile with a delay at the front of it.
                inputFile = webmURLDict[file["filename"]]
                fileName = str(interviewId) + "_p" + str(streamCount) + ".wav"
                outputFile = temp_dir + "/" + fileName

                # look at the bucket and
                key = 'Processed/' + interviewId + "/" + fileName
                objs = list(my_bucket.objects.filter(Prefix=key))
                while len(objs) > 0 and objs[0].key == key:
                    streamCount = streamCount + 1
                    fileName = str(interviewId) + "_p" + \
                        str(streamCount) + ".wav"
                    outputFile = temp_dir + "/" + fileName
                    key = 'Processed/' + interviewId + "/" + fileName
                    objs = list(my_bucket.objects.filter(Prefix=key))

                cmd = 'ffmpeg -y -loglevel warning -acodec libopus -i ' + inputFile + \
                    ' -af aresample=async=1,adelay=' + \
                    str(file['startTimeOffset']) + ' ' + outputFile

                p = subprocess.call(cmd, shell=True)

                ic(interviewId, "outputFile: ", outputFile)
                individualStreams.append(fileName)
                s3_client.upload_file(
                    outputFile, bucket, 'Processed/' + interviewId + "/" + fileName)

                # delete the individual stream from tmp after upload
                os.remove(outputFile)
                ic(interviewId, "Removed the file %s" % outputFile)
                streamCount = streamCount + 1
            except Exception as e:
                ic(interviewId, "Error processing stream", e)
                pass

        ic(interviewId, "Done processing individual streams")
        for stream in individualStreams:
            key = 'Processed/' + interviewId + '/' + stream
            inputs = inputs + " -i \"" + s3_client.generate_presigned_url(
                'get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=1000000) + "\"  "
        mixedFileName = "/mixed-" + interview + ".wav"
        cmd = "ffmpeg -y -loglevel warning" + inputs + " -filter_complex amix=inputs=" + \
            str(len(data["files"])) + \
            ":duration=longest:dropout_transition=3 " + temp_dir + mixedFileName

        ic(interviewId, "mixing streams", cmd)

        p = subprocess.call(cmd, shell=True)

        # check to see if it's already a multi part audio recording
        key = 'Processed/' + interviewId + "/" + interviewId + "_1.wav"
        objs = list(my_bucket.objects.filter(Prefix=key))
        ic(interviewId, "processing mix file. Uploaded to:")
        if len(objs) > 0 and objs[0].key == key:
            count = 3
            # check for interviewid_count.wav to make sure we're not overwriting. When we're not, upload.
            while (True):
                # check the bucket for the _count file
                key = 'Processed/' + interviewId + "/" + \
                    interviewId + "_" + str(count) + ".wav"
                objs = list(my_bucket.objects.filter(Prefix=key))
                if len(objs) > 0 and objs[0].key == key:
                    # if the key exists, increase the count
                    ic(interviewId, key, " exists. skipping count")
                else:
                    # if it doesn't, upload the file with that key.
                    s3_client.upload_file(temp_dir + mixedFileName, bucket, 'Processed/' +
                                          interviewId + "/" + interviewId + "_" + str(count) + ".wav")

                    ic(interviewId, bucket, 'Processed/' + interviewId +
                       "/" + interviewId + "_" + str(count) + ".wav")
                    break
                count = count + 1
        else:
            # if there isn't  a _1, see if there's a .wav
            key = 'Processed/' + interviewId + "/" + interviewId + ".wav"
            objs = list(my_bucket.objects.filter(Prefix=key))
            if len(objs) > 0 and objs[0].key == key:
                # if it does, rename interviewid.wav to interviewid_1.wav
                old_key = 'Processed/' + interviewId + "/" + interviewId + ".wav"
                new_key = key = 'Processed/' + interviewId + "/" + interviewId + "_1.wav"
                s3_resource.Object(bucket, new_key).copy_from(
                    CopySource=bucket + "/" + old_key)
                s3_resource.Object(bucket, old_key).delete()
                s3_client.upload_file(temp_dir + mixedFileName, bucket,
                                      'Processed/' + interviewId + "/" + interviewId + "_2.wav")
                ic(interviewId, bucket, 'Processed/' +
                   interviewId + "/" + interviewId + "_2.wav")
                ic(interviewId, "renamed ", old_key, " to ", new_key)
            else:
                # upload the file like normal
                s3_client.upload_file(temp_dir + mixedFileName, bucket,
                                      'Processed/' + interviewId + "/" + interviewId + ".wav")
                ic(interviewId, bucket, 'Processed/' +
                   interviewId + "/" + interviewId + ".wav")

        # delete the tmp folder
        shutil.rmtree(temp_dir)
        ic(interviewId, "Removed the folder %s" % temp_dir)

        # delete the non zip files
        objs = my_bucket.objects.filter(Prefix=unzippedLocation)
        for obj in objs:
            if (obj._key[-4:] != ".zip"):
                deletedObj = s3_client.delete_object(
                    Bucket=bucket, Key=obj._key)
                ic(interviewId, "deleted", bucket, obj._key)

        return "Re-Processed " + interviewId

    except Exception as e:
        jsonData["Status"] = "Failed"
        jsonData["Fail Status"] = e
        ic(interviewId, e)


if __name__ == "__main__":
    # read cli inputs
    parser = argparse.ArgumentParser()

    # is there an event param passed?
    parser.add_argument('--event', type=str, default="")
    args = parser.parse_args()

    if args.event != "":
        event = json.loads(args.event)
        context = ''

    lambda_handler(event, context)
