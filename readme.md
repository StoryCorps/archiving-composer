This code is used on the lambda script to convert webms to .wav files. 

It accepts a webhook (payload example below) for releavant information
```
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
The first three pieces are the important ones - 
id (archive id) tells the script where to find the .zip that contains the webms and json file; 
status - non upload status is ignored;
name - this text is split on :: and the first segment is used to name the files. 

I also run this code on my local when interviews need to be reprocessed. 
This is the case pretty rarely, but needs to happen when the lambda script has an error or the interview is larger than the 512 mb that lambda allows for storage. 
Local code in the local branch. 
