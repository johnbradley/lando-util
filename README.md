# lando-util
Utilities used by lando related to running a workflow
- download files from DukeDS, URLs, or with hard coded content
- organize output project directory
- upload a directory to DukeDS

## Install
```
python setup.py install
```

## Download Files
Users must first create a json command file with a list of items to download.

Run the download command:
```
python -m lando_util.download <COMMAND_FILE>
```

## Organize Output Project
Users must first create a json command file with settings to use when organizing the output project.

```
python -m lando_util.organize_project <COMMAND_FILE>
```

## Upload Directories
Users must first create a json command file with settings to use when uploading and sharing the output project.
The command will write out a json file with the resulting DukeDS project id and DukeDS README file id.
```
python -m lando_util.download <COMMAND_FILE> <OUTFILE>
```
