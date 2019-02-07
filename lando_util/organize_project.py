"""
Organizes an output project before uploading to a remote data store.

Directory structure:
results/           # this directory is uploaded in the store output stage (destination_dir in config)
   Methods.md      # document detailing methods used in workflow
   ...output files from workflow
   docs/
      README         # describes contents of the upload_directory
      logs/
          bespin-workflow-output.json   #stdout from cwl-runner - json job results
          bespin-workflow-output.log    #stderr from cwl-runner
          job-data.json                 # non-cwl job data used to create Bespin-Report.txt
      workflow/
          workflow.cwl            # cwl workflow we will run
          workflow.yml            # job order input file
"""
import os
import json
import shutil
import click


class Settings(object):
    METHODS_FILENAME = "Methods.md"
    README_FILENAME = "README"
    DOCS_DIRNAME = "docs"
    LOGS_DIRNAME = "logs"
    WORKFLOW_DIRNAME = "workflow"
    BESPIN_WORKFLOW_STDOUT_FILENAME = "bespin-workflow-output.json"
    BESPIN_WORKFLOW_STDERR_FILENAME = "bespin-workflow-output.log"
    JOB_DATA_FILENAME = "job-data.json"

    def __init__(self, cmdfile):
        data = json.load(cmdfile)
        self.destination_dir = data['destination_dir']  # directory where we will add files/folders
        self.workflow_path = data['workflow_path']  # path to the workflow we ran
        self.job_order_path = data['job_order_path']  # path to job order used when running the workflow
        self.job_data_path = data['job_data_path']  # path to data from Bespin about the job
        self.bespin_workflow_stdout_path = data['bespin_workflow_stdout_path']  # path to stdout created by CWL runner
        self.bespin_workflow_stderr_path = data['bespin_workflow_stderr_path']  # path to stderr created by CWL runner
        self.methods_template = data['methods_template']  # content of jinja template to build Readme.md

    @property
    def methods_dest_path(self):
        return os.path.join(self.destination_dir, self.METHODS_FILENAME)

    @property
    def docs_dir(self):
        return os.path.join(self.destination_dir, self.DOCS_DIRNAME)

    @property
    def readme_dest_path(self):
        return os.path.join(self.docs_dir, self.README_FILENAME)

    @property
    def logs_dir(self):
        return os.path.join(self.docs_dir, self.LOGS_DIRNAME)

    @property
    def bespin_workflow_stdout_dest_path(self):
        return os.path.join(self.logs_dir, self.BESPIN_WORKFLOW_STDOUT_FILENAME)

    @property
    def bespin_workflow_stderr_dest_path(self):
        return os.path.join(self.logs_dir, self.BESPIN_WORKFLOW_STDERR_FILENAME)

    @property
    def job_data_dest_path(self):
        return os.path.join(self.logs_dir, self.JOB_DATA_FILENAME)

    @property
    def workflow_dir(self):
        return os.path.join(self.docs_dir, self.WORKFLOW_DIRNAME)

    @property
    def workflow_dest_path(self):
        return os.path.join(self.workflow_dir, os.path.basename(self.workflow_path))

    @property
    def job_order_dest_path(self):
        return os.path.join(self.workflow_dir, os.path.basename(self.job_order_path))


class Organizer(object):
    def __init__(self, settings):
        self.settings = settings

    def run(self):
        # create all new directories
        os.makedirs(name=self.settings.docs_dir, exist_ok=True)
        os.makedirs(name=self.settings.logs_dir, exist_ok=True)
        os.makedirs(name=self.settings.workflow_dir, exist_ok=True)

        # create files
        self.create_methods_document()
        self.create_readme_document()

        # copy files
        shutil.copy(self.settings.bespin_workflow_stdout_path, self.settings.bespin_workflow_stdout_dest_path)
        shutil.copy(self.settings.bespin_workflow_stderr_path, self.settings.bespin_workflow_stderr_dest_path)
        shutil.copy(self.settings.job_data_path, self.settings.job_data_dest_path)
        shutil.copy(self.settings.workflow_path, self.settings.workflow_dest_path)
        shutil.copy(self.settings.job_order_path, self.settings.job_order_dest_path)

    def create_methods_document(self):
        click.echo("TODO methods document {} ".format(self.settings.methods_dest_path))

    def create_readme_document(self):
        click.echo("TODO methods document {} ".format(self.settings.readme_dest_path))


@click.command()
@click.argument('cmdfile', type=click.File())
def organize_project(cmdfile):
    settings = Settings(cmdfile)
    organizer = Organizer(settings)
    organizer.run()


if __name__ == '__main__':
    organize_project()
