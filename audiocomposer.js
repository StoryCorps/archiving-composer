#!/usr/bin/env node

var fs = require("fs"),
  util = require("util"),
  exec = require("child_process").execSync,
  fs = require("fs"),
  program = require("commander"),
  path = require("path"),
  unzip = require("unzip"),
  child;

program
  .version("0.0.1")
  .usage("[options] -i <zipFile>")
  .option("-i, --input <zipFile>", "Archive ZIP file")
  .option("-f, --format [type]", "Output format [webm,mp4]", "webm")
  .parse(process.argv);

if (!program.input) {
  program.help();
}

var zip_file = program.input;
var dirname = path.dirname(zip_file);
var basename = path.basename(zip_file, ".zip");
var temp_dir = path.join(dirname, basename);

// Unzip the archive
var input = fs.createReadStream(zip_file);
var result = input.pipe(unzip.Extract({ path: temp_dir }));

result.on("close", function () {
  var files = fs.readdirSync(temp_dir);

  var json_file;
  files.forEach(function (file) {
    if (path.extname(file) == ".json") {
      json_file = file;
    }
  });

  if (!json_file) {
    console.log("ZIP file does not contain a json file");
  }

  var script = JSON.parse(
    fs.readFileSync(path.join(temp_dir, json_file)).toString()
  );
  console.log(script);

  var archiveId = script.id;

  var archive_path = temp_dir;

  var format = program.format;

  var startTime = 10000000000000;
  var endTime = 0;
  // find start end end time for the whole playback
  script.files.forEach(function (e) {
    if (e.startTimeOffset < startTime) {
      startTime = e.startTimeOffset;
    }
    if (e.stopTimeOffset > endTime) {
      endTime = e.stopTimeOffset;
    }
  });

  // make them all 0 based
  script.files.forEach(function (e) {
    e.startTimeOffset -= startTime;
    e.stopTimeOffset -= startTime;
  });

  // sort them by start time
  script.files.sort(function (a, b) {
    return a.startTimeOffset - b.startTimeOffset;
  });

  console.log("duration=", endTime - startTime);

  var inputs = "";

  // Loop over the files to Create a WAV file for each path that has the same offset at the start.
  script.files.forEach((oneFile) => {

    let fullPath = `${archive_path}/${oneFile.filename}`;
    cmd = `ffmpeg -i ${fullPath} -af "adelay=${oneFile.startTimeOffset}|${oneFile.startTimeOffset}" ${fullPath}.wav`;
    child = exec(cmd, function (error, stdout, stderr) {
      if (error !== null) {
        console.log("exec error: " + error);
      }
    });

    inputs += ` -itsoffset ${oneFile.startTimeOffset} -i ${oneFile.filename}.wav `;
  });

  // now mix it down into one wav file.
  cmd = `ffmpeg ${inputs} -filter_complex amix=inputs=${script.files.length}:duration=longest:dropout_transition=3 testoutput.wav`;

  child = exec(cmd, function (error, stdout, stderr) {
    if (error !== null) {
      console.log("Mixdown error: " + error);
    }
  });

  //   // remove temp files
  //   fs.unlinkSync(archiveId + "-list.txt");
  //   chunks.forEach(function(chunk) {
  //     console.log("Removing", chunk);
  //     fs.unlinkSync(chunk);
  //   });
});
