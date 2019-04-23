import click
import json
import os
import zipfile
import urllib.request
from ddsc.sdk.client import Client as DukeDSClient


def get_stage_items(cmdfile):
    data = json.load(cmdfile)
    items = []
    for file_data in data['items']:
        item_type = file_data['type']
        source = file_data['source']
        dest = file_data['dest']
        unzip_to = file_data.get('unzip_to')
        items.append((item_type, source, dest, unzip_to))
    return items


def stage_data(dds_client, stage_items):
    downloaded_metadata_items = []
    click.echo("Staging {} items.".format(len(stage_items)))
    for item_type, source, dest, unzip_to in stage_items:
        parent_directory = os.path.dirname(dest)
        os.makedirs(parent_directory, exist_ok=True)
        if item_type == "DukeDS":
            click.echo("Downloading DukeDS file {} to {}.".format(source, dest))
            dds_file = dds_client.get_file_by_id(file_id=source)
            dds_file.download_to_path(dest)
            downloaded_metadata_items.append(dds_file._data_dict)
        elif item_type == "url":
            click.echo("Downloading URL {} to {}.".format(source, dest))
            urllib.request.urlretrieve(source, dest)
        elif item_type == "write":
            click.echo("Writing file {}.".format(dest))
            with open(dest, 'w') as outfile:
                outfile.write(source)
        else:
            raise ValueError("Unsupported type {}".format(item_type))
        if unzip_to:
            click.echo("Unzip file {} to {}.".format(dest, unzip_to))
            with zipfile.ZipFile(dest) as z:
                z.extractall(unzip_to)
    click.echo("Staging complete.".format(len(stage_items)))
    return downloaded_metadata_items


def write_downloaded_metadata(outfile, downloaded_metadata_items):
    click.echo("Writing {} metadata items to {}.".format(len(downloaded_metadata_items), outfile.name))
    outfile.write(json.dumps({
        "items": downloaded_metadata_items
    }))


@click.command()
@click.argument('cmdfile', type=click.File())
@click.argument('downloaded_metadata_file', type=click.File('w'), required=False)
def main(cmdfile, downloaded_metadata_file):
    dds_client = DukeDSClient()
    stage_items = get_stage_items(cmdfile)
    downloaded_metadata_items = stage_data(dds_client, stage_items)
    if downloaded_metadata_file:
        write_downloaded_metadata(downloaded_metadata_file, downloaded_metadata_items)


if __name__ == '__main__':
    main()
