from unittest import TestCase
from unittest.mock import patch, Mock, call
from lando_util.organize_project import Settings, Organizer


class TestSettings(TestCase):
    @patch('lando_util.organize_project.json')
    def test_properties(self, mock_json):
        mock_json.load.return_value = {
            "destination_dir": 'somedir',
            "workflow_path": '/workflow/sort.cwl',
            "job_order_path": '/output/job_order.json',
            "job_data_path": '/output/job_order.jsonjob_data.json',
            "bespin_workflow_stdout_path": '/output/workflow-output.json',
            "bespin_workflow_stderr_path": '/output/workflow-output.log',
            "methods_template": '#replace stuff',
        }
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.methods_dest_path, 'somedir/Methods.md')
        self.assertEqual(settings.docs_dir, 'somedir/docs')
        self.assertEqual(settings.readme_dest_path, 'somedir/docs/README')
        self.assertEqual(settings.logs_dir, 'somedir/docs/logs')
        self.assertEqual(settings.bespin_workflow_stdout_dest_path, 'somedir/docs/logs/bespin-workflow-output.json')
        self.assertEqual(settings.bespin_workflow_stderr_dest_path, 'somedir/docs/logs/bespin-workflow-output.log')
        self.assertEqual(settings.job_data_dest_path, 'somedir/docs/logs/job-data.json')
        self.assertEqual(settings.workflow_dir, 'somedir/docs/workflow')
        self.assertEqual(settings.workflow_dest_path, 'somedir/docs/workflow/sort.cwl')
        self.assertEqual(settings.job_order_dest_path, 'somedir/docs/workflow/job_order.json')


class TestOrganizer(TestCase):
    @patch('lando_util.organize_project.os')
    @patch('lando_util.organize_project.shutil')
    def test_run(self, mock_shutil, mock_os):
        mock_settings = Mock()
        organizer = Organizer(mock_settings)
        organizer.run()

        mock_os.makedirs.assert_has_calls([
            call(exist_ok=True, name=mock_settings.docs_dir),
            call(exist_ok=True, name=mock_settings.logs_dir),
            call(exist_ok=True, name=mock_settings.workflow_dir),
        ])
        mock_shutil.copy.assert_has_calls([
            call(mock_settings.bespin_workflow_stdout_path, mock_settings.bespin_workflow_stdout_dest_path),
            call(mock_settings.bespin_workflow_stderr_path, mock_settings.bespin_workflow_stderr_dest_path),
            call(mock_settings.job_data_path, mock_settings.job_data_dest_path),
            call(mock_settings.workflow_path, mock_settings.workflow_dest_path),
            call(mock_settings.job_order_path, mock_settings.job_order_dest_path),
        ])
