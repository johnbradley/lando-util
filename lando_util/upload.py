import click
import json
from ddsc.sdk.client import Client as DukeDSClient
from ddsc.core.upload import ProjectUpload
from ddsc.core.remotestore import RemoteStore, ProjectNameOrId
from ddsc.core.d4s2 import D4S2Project


class UploadList(object):
    def __init__(self, cmdfile):
        data = json.load(cmdfile)
        self.destination = data['destination']
        self.paths = data['paths']
        share = data.get('share', {})
        self.share_dds_user_ids = share['dds_user_ids']
        self.share_auth_role = share.get('auth_role', 'project_admin')
        self.share_user_message = share.get('user_message', 'Bespin job results.')


def write_results(project_id, outfile):
    click.echo("Writing project id {} to {}".format(project_id, outfile.name))
    contents = json.dumps({
        'project_id': project_id,
        'readme_file_id': 'TODO',
    })
    outfile.write(contents)
    outfile.close()


def share_project(dds_client, share_project_id, upload_list):
    config = dds_client.dds_connection.config
    remote_store = RemoteStore(config)
    remote_project = remote_store.fetch_remote_project_by_id(share_project_id)
    d4s2_project = D4S2Project(config, remote_store, print_func=print)
    for dds_user_id in upload_list.share_dds_user_ids:
        d4s2_project.share(remote_project,
                           remote_store.fetch_user(dds_user_id),
                           force_send=True,
                           auth_role=upload_list.share_auth_role,
                           user_message=upload_list.share_user_message)


def upload_files(dds_client, upload_list, outfile):
    click.echo("Uploading {} paths to {}.".format(len(upload_list.paths), upload_list.destination))
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
        share_project(dds_client, project.id, upload_list)
    else:
        project.delete()
        raise ValueError("Error: No files or folders found to upload.")


@click.command()
@click.argument('cmdfile', type=click.File('r'))
@click.argument('outfile', type=click.File('w'))
def main(cmdfile, outfile):
    dds_client = DukeDSClient()
    upload_list = UploadList(cmdfile)
    upload_files(dds_client, upload_list, outfile)


if __name__ == '__main__':
    main()
