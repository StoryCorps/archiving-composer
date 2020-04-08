# Background
This tool is based on a demo by Vonage. Its purpose is to take audio-only OpenTok archives and convert them into WAV files and a mixed down single WAV file.


## Installing

You need to make sure you have installed FFmpeg with all of the dependencies. On Mac OS you do this with:

`brew install ffmpeg $(brew options ffmpeg | grep -vE '\s' | grep -- '--with-' | tr '\n' ' ')`

Then checkout this repo and run `npm install`.

## Usage

```
  Usage: ./audiocomposer.js [options] -i <zipFile>

  Options:

    -h, --help             output usage information
    -V, --version          output the version number
    -i, --input <zipFile>  Archive ZIP file
```

The ZIP file is the output of the OpenTok individual stream archiving API.
