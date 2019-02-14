import click
import json
from ddsc.sdk.client import Client as DukeDSClient
from ddsc.core.upload import ProjectUpload
from ddsc.core.remotestore import RemoteStore, ProjectNameOrId
from ddsc.core.d4s2 import D4S2Project


class Settings(object):
    def __init__(self, cmdfile):
        data = json.load(cmdfile)
        self.destination = data['destination']
        self.readme_file_path = data['readme_file_path']
        self.paths = data['paths']
        share = data.get('share', {})
        self.share_dds_user_ids = share['dds_user_ids']
        self.share_auth_role = share.get('auth_role', 'project_admin')
        self.share_user_message = share.get('user_message', 'Bespin job results.')


class NothingToUploadException(Exception):
    pass


class UploadUtil(object):
    def __init__(self, cmdfile):
        self.settings = Settings(cmdfile)
        self.dds_client = DukeDSClient()
        self.dds_config = self.dds_client.dds_connection.config

    def create_project(self):
        project_name = self.settings.destination
        return self.dds_client.create_project(project_name, description=project_name)

    def upload_files(self, project):
        project_upload = ProjectUpload(self.dds_config,
                                       ProjectNameOrId.create_from_project_id(project.id),
                                       self.settings.paths)
        click.echo(project_upload.get_differences_summary())
        if project_upload.needs_to_upload():
            click.echo("Uploading")
            project_upload.run()
        else:
            raise NothingToUploadException("Error: No files or folders found to upload.")

    def share_project(self, project):
        remote_store = RemoteStore(self.dds_config)
        remote_project = remote_store.fetch_remote_project_by_id(project.id)
        d4s2_project = D4S2Project(self.dds_config, remote_store, print_func=print)
        for dds_user_id in self.settings.share_dds_user_ids:
            d4s2_project.share(remote_project,
                               remote_store.fetch_user(dds_user_id),
                               force_send=True,
                               auth_role=self.settings.share_auth_role,
                               user_message=self.settings.share_user_message)

    def create_annotate_project_details_script(self, project, outfile):
        readme_file = project.get_child_for_path(self.settings.readme_file_path)
        click.echo("Writing annotate project details script project_id:{} readme_file_id:{} to {}".format(
            project.id, readme_file.id, outfile.name))
        contents = "kubectl annotate pod $MY_POD_NAME " \
                   "project_id={} readme_file_id={}".format(project.id, readme_file.id)
        outfile.write(contents)
        outfile.close()


@click.command()
@click.argument('cmdfile', type=click.File('r'))
@click.argument('outfile', type=click.File('w'))
def main(cmdfile, outfile):
    util = UploadUtil(cmdfile)
    project = util.create_project()
    try:
        util.upload_files(project)
        util.share_project(project)
        util.create_annotate_project_details_script(project, outfile)
    except NothingToUploadException:
        project.delete()
        raise


if __name__ == '__main__':
    main()
