# lando-util
Utilities used by [k8s.lando](https://github.com/Duke-GCB/lando/blob/master/lando/k8s/README.md) related to running a workflow.
- download files from DukeDS, URLs, or with hard coded content
- organize output project directory
- upload a directory to DukeDS

These utilities are meant to be run inside a k8s container by `k8s.lando`.
This logic was broken out of [lando_worker](https://github.com/Duke-GCB/lando/tree/master/lando/worker) to be simplier to understand, maintain and replace. The methods to download, organize directories and upload are baked into the `lando_worker` VM, but in the future `lando worker` can be simplified to use these containerized utilties also.

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
python -m lando_util.upload <COMMAND_FILE> <OUTFILE>
```