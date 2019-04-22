# lando-util
Utilities used by [k8s.lando](https://github.com/Duke-GCB/lando/blob/master/lando/k8s/README.md) related to running a workflow.
- stage data from DukeDS, URLs, hard coded content, etc
- organize output project directory
- upload a directory to DukeDS

These utilities are meant to be run inside a k8s container by `k8s.lando`.
This logic was broken out of [lando_worker](https://github.com/Duke-GCB/lando/tree/master/lando/worker) to be simplier to understand, maintain and replace. The methods to download, organize directories and upload are baked into the `lando_worker` VM, but in the future `lando worker` can be simplified to use these containerized utilties also.

## Requirements
- [python](https://www.python.org/) - version 3.3+

## Install
```
python setup.py install
```

## Stage Data
Users must first create a json command file with a list of items to stage.

Run the stagedata command:
```
python -m lando_util.stagedata <COMMAND_FILE> [DOWNLOADED_ITEMS_METADATA_FILE]
```
DOWNLOADED_ITEMS_METADATA_FILE is an optional argument that will save metadata about downloaded DukeDS files.

Example JSON command file:
```
{
    "items": [
        {"type": "DukeDS", "source": "<DukeDS file id>", "dest": "<path to save file to>"},
        {"type": "url", "source": "<url of file to download>", "dest": "<path to save file to>"},
        {"type": "write", "source": "<data to write>", "dest": "<path to write data to>"},
    ]
}
```
Supported values for type are:
- DukeDS - The `source` field must be a DukeDS file UUID.
- url - The `source` field must be a url of a file to download.
- write - The `source` field must be data to be writen to a file.
- unzip - Unzip `source` field to `dest`.


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

JSON command file:
```
{
    "destination": "<project name>",
    "readme_file_path": "<path to readme file>",
    "paths": ["<Path to folder or file to upload>"],
    "share": {
        "dds_user_ids": ["<DukeDS user id to share with>"],
        "auth_role": "<DukeDS auth role to grant to dds_user_ids users>",  // optional field
        "user_message": "<Message to include in the share email>"  // optional field
    },
    "activity": {
        "name": "<name of the activity to be created>",
        "description": "<description of the activity>",
        "started_on": "<datetime when activity started>",
        "ended_on": "<datetime when activity ended>",
        "input_file_versions_json_path": "<path to JSON file of metadata about files used in activity>",
        "workflow_output_json_path": "<path to cwl runner stdout json file>"
    }
}
```

