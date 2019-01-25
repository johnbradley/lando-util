import click
import json
from ddsc.sdk.client import Client as DukeDSClient
from ddsc.core.upload import ProjectUpload
from ddsc.core.remotestore import ProjectNameOrId


class UploadList(object):
    def __init__(self, cmdfile):
        data = json.load(cmdfile)
        self.destination = data['destination']
        self.paths = data['paths']


def write_results(project_id, outfile):
    click.echo("Writing project id {} to {}".format(project_id, outfile.name))
    contents = json.dumps({
        'project_id': project_id
    })
    outfile.write(contents)
    outfile.close()


@click.command()
@click.argument('cmdfile', type=click.File('r'))
@click.argument('outfile', type=click.File('w'))
def upload_files(cmdfile, outfile):
    upload_list = UploadList(cmdfile)
    click.echo("Uploading {} paths to {}.".format(len(upload_list.paths), upload_list.destination))
    dds_client = DukeDSClient()
    project_name = upload_list.destination
    project = dds_client.create_project(project_name, description=project_name)
    project_upload = ProjectUpload(dds_client.dds_connection.config,
                                   ProjectNameOrId.create_from_project_id(project.id),
                                   upload_list.paths)
    click.echo(project_upload.get_differences_summary())
    if project_upload.needs_to_upload():
        click.echo("Uploading")
        project_upload.run()
        write_results(project.id, outfile)
    else:
        click.echo("Nothing needs to be uploaded.")


if __name__ == '__main__':
    upload_files()
