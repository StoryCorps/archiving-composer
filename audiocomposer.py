from __future__ import print_function

import urllib
import zipfile
import boto3
import io
import os
import json
import subprocess
import re

event = ""   #for local testing
context = "" #for local testing


def lambda_handler(event, context):
    tmp = '/tmp/'
    event = json.load(open('event.json')) #for testing local
    tmp = './tmp/' # for local testing
    body = json.loads(event["body"])
    print("event:", event)
    print("body:", body)
    
    bucket = "storycorps-signature-remote"
    account = str(body["partnerId"])
    interview = str(body["id"])
    interviewId = str(re.split('::',body["name"])[0])
    status = body["status"]
    
    if (status != "uploaded"):
        print(interviewId, "not an upload event.", status )
        return (interviewId, "not not an upload event", status)

    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket)

    zippedKey = account + "/" + interview + "/archive.zip"
    unzippedLocation = account + "/" + interview
    temp_dir = tmp + interview
    interviewId = interviewId.lower()
    try:
        key = zippedKey
        print("downloading and unzipping", bucket, key)
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        putObjects = []
        with io.BytesIO(obj["Body"].read()) as tf:
            # Read the file as a zipfile and process the members
            with zipfile.ZipFile(tf, mode='r') as zipf:
                for file in zipf.infolist():
                    fileName = account + "/" + interview + "/" + file.filename
                    putFile = s3_client.put_object(Bucket=bucket, Key=fileName, Body=zipf.read(file))
                    putObjects.append(putFile)

        # for each object in the bucket/account/archiveID directory
        objs = my_bucket.objects.filter(Prefix=unzippedLocation)
        #make a folder in tmp
        print("creating folder", tmp,  interview)
        if not os.path.exists(tmp + interview):
                os.makedirs(tmp + interview)
        #download the files
        for obj in objs:
            if(obj._key[-5:] == ".json"):
                s3_client.download_file(bucket, obj.key, tmp + interview + "/interview.json")
            elif(obj._key[-5:] == ".webm" == ".webm"):
                # webmLocalKey = tmp + re.split('/',obj.key)[1] + re.split('/',obj.key)[]
                s3_client.download_file(bucket, obj.key, tmp + obj.key[-78:])
            pass
        
        # open the JSON file 
        f = open(tmp + interview + '/interview.json',) 
        
        # returns JSON object as a dictionary 
        data = json.load(f)
        startTime = 10000000000000;
        endTime = 0;
        
        # find start end end time for the whole playback
        for file in data['files']: 
            if(file["startTimeOffset"] < startTime):
                startTime = file["startTimeOffset"]
            if(file["stopTimeOffset"] > endTime):
                endTime = file["stopTimeOffset"]

        for file in data['files']: 
            file["startTimeOffset"] -= startTime
            file["stopTimeOffset"] -= endTime
        # print("script=",data);
        # print("duration=", endTime - startTime);

        inputs = ""
        streamCount = 1
        for file in data['files']: 
            # generate a single wavefile with a delay at the front of it.
            inputFile = temp_dir + "/" + file["filename"]
            fileName = str(interviewId) + "_p" + str(streamCount) + ".wav"
            outputFile = temp_dir + "/" + fileName

            key = 'Processed/' + interviewId + "/" + fileName
            objs = list(my_bucket.objects.filter(Prefix=key))
            while len(objs) > 0 and objs[0].key == key:
                streamCount = streamCount + 1
                fileName = str(interviewId) + "_p" + str(streamCount) + ".wav"
                key = 'Processed/' + interviewId + "/" + fileName
                objs = list(my_bucket.objects.filter(Prefix=key))


            cmd = "ffmpeg -y -loglevel warning -acodec libopus -i " + inputFile + " -af adelay=" + str(file["startTimeOffset"]) + " " + outputFile
            print("cmd: ", cmd)
            p = subprocess.call(cmd, shell=True)
            
            print("outputFile: ", outputFile)
            s3_client.upload_file(outputFile, bucket, 'Processed/' + interviewId + "/" + fileName)
            inputs += " -itsoffset " + str(file["startTimeOffset"]) + " -acodec libopus -i " + inputFile
            streamCount = streamCount + 1

        mixedFileName = "/mixed-" + interview + ".wav"
        cmd = "ffmpeg -y -loglevel warning" + inputs + " -filter_complex amix=inputs=" + str(len(data["files"])) + ":duration=longest:dropout_transition=3 " + temp_dir + mixedFileName
        p = subprocess.call(cmd, shell=True)  

        #check to see if it's already a multi part audio recording
        key = 'Processed/' + interviewId + "/" + interviewId + "_1.wav"
        objs = list(my_bucket.objects.filter(Prefix=key))
        print("Uploaded to:")
        if len(objs) > 0 and objs[0].key == key:
            count = 3
            #check for interviewid_count.wav to make sure we're not overwriting. When we're not, upload. 
            while(True):
                # check the bucket for the _count file 
                key = 'Processed/' + interviewId + "/" + interviewId + "_" + str(count) + ".wav"
                objs = list(my_bucket.objects.filter(Prefix=key))
                if len(objs) > 0 and objs[0].key == key:
                    #if the key exists, increase the count
                    print(key, " exists. skipping count")
                else:
                    #if it doesn't, upload the file with that key. 
                    s3_client.upload_file(temp_dir + mixedFileName, bucket, 'Processed/' + interviewId + "/" + interviewId + "_" + str(count) + ".wav")
                    print(bucket, 'Processed/' + interviewId + "/" + interviewId + "_" + str(count) + ".wav")
                    break
                count = count + 1 
        else:
            #if there isn't  a _1, see if there's a .wav
            key = 'Processed/' + interviewId + "/" + interviewId + ".wav"
            objs = list(my_bucket.objects.filter(Prefix=key))
            if len(objs) > 0 and objs[0].key == key:
                #if it does, rename interviewid.wav to interviewid_1.wav
                old_key = 'Processed/' + interviewId + "/" + interviewId + ".wav"
                new_key = key = 'Processed/' + interviewId + "/" + interviewId + "_1.wav"
                s3_resource.Object(bucket,new_key).copy_from(CopySource= bucket + "/" + old_key)
                s3_resource.Object(bucket,old_key).delete()
                s3_client.upload_file(temp_dir + mixedFileName, bucket, 'Processed/' + interviewId + "/" + interviewId + "_2.wav")
                print(bucket, 'Processed/' + interviewId + "/" + interviewId + "_2.wav")
                print("renamed ", old_key, " to ", new_key)
            else:
                #upload the file like normal
                s3_client.upload_file(temp_dir + mixedFileName, bucket, 'Processed/' + interviewId + "/" + interviewId + ".wav")
                print(bucket, 'Processed/' + interviewId + "/" + interviewId + ".wav")

        #delete the non zip files
        objs = my_bucket.objects.filter(Prefix=unzippedLocation)
        for obj in objs:
            if(obj._key[-4:] != ".zip"):
                deletedObj = s3_client.delete_object(Bucket=bucket, Key=obj._key)
                print("deleted", bucket, obj._key)
        print("done with", interviewId)
    except Exception as e:
        print(e)
        raise e

lambda_handler(event, context)