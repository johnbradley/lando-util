from unittest import TestCase
from unittest.mock import patch, Mock, call, mock_open, create_autospec
from lando_util.organize_project.organizer import write_data_to_file, Settings, ProjectData, Organizer
import json
import os


class TestOrganizerFuncs(TestCase):
    def test_write_data_to_file(self):
        mocked_open = mock_open()
        with patch('builtins.open', mocked_open, create=True):
            write_data_to_file(data='somedata', filepath='/tmp/somepath.txt')
        mocked_open.assert_called_with('/tmp/somepath.txt', 'w')
        mocked_open.return_value.write.assert_called_with('somedata')


class TestSettings(TestCase):
    def setUp(self):
        self.settings_packed_dict = {
            "bespin_job_id": "1",
            "destination_dir": 'somedir',
            "workflow_path": '/workflow/sort.cwl',
            "workflow_to_read": '/workflow/read/sort.cwl',
            "workflow_type": "packed",
            "job_order_path": '/output/job_order.json',
            "bespin_workflow_stdout_path": '/output/workflow-output.json',
            "bespin_workflow_stderr_path": '/output/workflow-output.log',
            "bespin_workflow_started": "2019-02-07T12:30",
            "bespin_workflow_finished": "2019-02-07T12:45",
            "methods_template": '#replace stuff',
            "additional_log_files": [
                "/bespin/output-data/job-51-bob-resource-usage.json",
            ]
        }
        self.settings_zipped_dict = {
            "bespin_job_id": "1",
            "destination_dir": 'somedir',
            "workflow_path": '/workflow/sort.cwl',
            "workflow_to_read": '/workflow/read/sort.zip',
            "workflow_type": "zipped",
            "job_order_path": '/output/job_order.json',
            "bespin_workflow_stdout_path": '/output/workflow-output.json',
            "bespin_workflow_stderr_path": '/output/workflow-output.log',
            "bespin_workflow_started": "2019-02-07T12:30",
            "bespin_workflow_finished": "2019-02-07T12:45",
            "methods_template": '#replace stuff',
            "additional_log_files": [
                "/bespin/output-data/job-51-bob-resource-usage.json",
            ]
        }

    @patch('lando_util.organize_project.organizer.json')
    def test_packed_properties(self, mock_json):
        mock_json.load.return_value = self.settings_packed_dict
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.docs_dir, 'somedir/docs')
        self.assertEqual(settings.readme_md_dest_path, 'somedir/docs/README.md')
        self.assertEqual(settings.readme_html_dest_path, 'somedir/docs/README.html')
        self.assertEqual(settings.logs_dir, 'somedir/docs/logs')
        self.assertEqual(settings.bespin_workflow_stdout_dest_path, 'somedir/docs/logs/bespin-workflow-output.json')
        self.assertEqual(settings.bespin_workflow_stderr_dest_path, 'somedir/docs/logs/bespin-workflow-output.log')
        self.assertEqual(settings.job_data_dest_path, 'somedir/docs/logs/job-data.json')
        self.assertEqual(settings.scripts_dir, 'somedir/docs/scripts')
        self.assertEqual(settings.workflow_dest_path, 'somedir/docs/scripts/sort.cwl')
        self.assertEqual(settings.job_order_dest_path, 'somedir/docs/scripts/job_order.json')
        self.assertEqual(settings.bespin_workflow_elapsed_minutes, 15.0)
        self.assertEqual(settings.additional_log_files, ["/bespin/output-data/job-51-bob-resource-usage.json"])
        self.assertEqual(settings.workflow_path, '/workflow/sort.cwl')
        self.assertEqual(settings.workflow_to_read, '/workflow/read/sort.cwl')
        self.assertEqual(settings.workflow_type, 'packed')

    @patch('lando_util.organize_project.organizer.json')
    def test_zipped_properties(self, mock_json):
        mock_json.load.return_value = self.settings_zipped_dict
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.docs_dir, 'somedir/docs')
        self.assertEqual(settings.readme_md_dest_path, 'somedir/docs/README.md')
        self.assertEqual(settings.readme_html_dest_path, 'somedir/docs/README.html')
        self.assertEqual(settings.logs_dir, 'somedir/docs/logs')
        self.assertEqual(settings.bespin_workflow_stdout_dest_path, 'somedir/docs/logs/bespin-workflow-output.json')
        self.assertEqual(settings.bespin_workflow_stderr_dest_path, 'somedir/docs/logs/bespin-workflow-output.log')
        self.assertEqual(settings.job_data_dest_path, 'somedir/docs/logs/job-data.json')
        self.assertEqual(settings.scripts_dir, 'somedir/docs/scripts')
        self.assertEqual(settings.workflow_dest_path, 'somedir/docs/scripts/sort.cwl')
        self.assertEqual(settings.job_order_dest_path, 'somedir/docs/scripts/job_order.json')
        self.assertEqual(settings.bespin_workflow_elapsed_minutes, 15.0)
        self.assertEqual(settings.additional_log_files, ["/bespin/output-data/job-51-bob-resource-usage.json"])
        self.assertEqual(settings.workflow_path, '/workflow/sort.cwl')
        self.assertEqual(settings.workflow_to_read, '/workflow/read/sort.zip')
        self.assertEqual(settings.workflow_type, 'zipped')

    @patch('lando_util.organize_project.organizer.json')
    def test_bespin_workflow_elapsed_minutes(self, mock_json):
        self.settings_packed_dict['bespin_workflow_started'] = '2019-02-07T12:30'
        self.settings_packed_dict['bespin_workflow_finished'] = '2019-02-09T12:30'
        mock_json.load.return_value = self.settings_packed_dict
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.bespin_workflow_elapsed_minutes, 2 * 24 * 60)

    @patch('lando_util.organize_project.organizer.json')
    def test_bespin_workflow_elapsed_minutes_is_optional(self, mock_json):
        del self.settings_packed_dict['bespin_workflow_started']
        del self.settings_packed_dict['bespin_workflow_finished']
        mock_json.load.return_value = self.settings_packed_dict
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.bespin_workflow_elapsed_minutes, 0)


class TestProjectData(TestCase):
    @patch('lando_util.organize_project.organizer.create_workflow_info')
    @patch('lando_util.organize_project.organizer.ReadmeReport')
    def test_constructor(self, mock_readme_report, mock_create_workflow_info):
        mock_settings = Mock(
            bespin_job_id='92',
            bespin_workflow_started='2019-02-07T12:30',
            bespin_workflow_finished='2019-02-09T12:45',
            bespin_workflow_elapsed_minutes='120',
            workflow_to_read='/input/read/workflow.cwl',
            workflow_path='/input/sort.cwl',
            job_order_path='/data/job_order.json',
            bespin_workflow_stdout_path='/output/workflow_stdout.json',
            methods_template='#Markdown'
        )
        mock_create_workflow_info.return_value.count_output_files.return_value = 13
        mock_create_workflow_info.return_value.total_file_size_str.return_value = '20 GiB'

        project_data = ProjectData(mock_settings)

        mock_create_workflow_info.assert_called_with('/input/read/workflow.cwl')
        self.assertEqual(project_data.workflow_info, mock_create_workflow_info.return_value)
        mock_workflow_info = mock_create_workflow_info.return_value
        mock_workflow_info.update_with_job_order.assert_called_with(job_order_path='/data/job_order.json')
        mock_workflow_info.update_with_job_output.assert_called_with(job_output_path='/output/workflow_stdout.json')

        self.assertEqual(project_data.readme_report, mock_readme_report.return_value)
        expected_job_data = {
            'id': '92',
            'started': '2019-02-07T12:30',
            'finished': '2019-02-09T12:45',
            'run_time': '120 minutes',
            'num_output_files': 13,
            'total_file_size_str': '20 GiB',
        }
        mock_readme_report.assert_called_with(project_data.workflow_info, expected_job_data)
        self.assertEqual(project_data.job_data, expected_job_data)


class TestOrganizer(TestCase):
    @patch('lando_util.organize_project.organizer.os')
    @patch('lando_util.organize_project.organizer.shutil')
    @patch('lando_util.organize_project.organizer.ProjectData')
    @patch('lando_util.organize_project.organizer.write_data_to_file')
    def test_run_packed(self, mock_write_data_to_file, mock_project_data, mock_shutil, mock_os):
        mock_settings = Mock()
        mock_settings.workflow_type = 'packed'
        mock_settings.bespin_job_id = '42'
        mock_settings.bespin_workflow_started = '2019-02-07T12:30'
        mock_settings.bespin_workflow_finished = '2019-02-09T12:45'
        mock_settings.bespin_workflow_elapsed_minutes = '120'
        mock_settings.logs_dir = '/results/docs/logs/'
        mock_settings.additional_log_files = ['/tmp/extra/usage-report.txt', '/data/log2.txt']
        mock_settings.job_data = {}
        mock_project_data.return_value = Mock(
            methods_template='#Markdown',
            job_data={
                'id': '42',
            }
        )
        mock_os.path = os.path

        organizer = Organizer(mock_settings)
        organizer.run()

        mock_os.makedirs.assert_has_calls([
            call(exist_ok=True, name=mock_settings.docs_dir),
            call(exist_ok=True, name=mock_settings.scripts_dir),
            call(exist_ok=True, name=mock_settings.logs_dir),
        ])
        mock_shutil.copy.assert_has_calls([
            call(mock_settings.workflow_path, mock_settings.workflow_dest_path),
            call(mock_settings.job_order_path, mock_settings.job_order_dest_path),
            call(mock_settings.bespin_workflow_stdout_path, mock_settings.bespin_workflow_stdout_dest_path),
            call(mock_settings.bespin_workflow_stderr_path, mock_settings.bespin_workflow_stderr_dest_path),
            call('/tmp/extra/usage-report.txt', '/results/docs/logs/usage-report.txt'),
            call('/data/log2.txt', '/results/docs/logs/log2.txt'),
        ])
        project_data = mock_project_data.return_value
        mock_write_data_to_file.assert_has_calls([
            call(data=project_data.readme_report.render_markdown.return_value,
                 filepath=mock_settings.readme_md_dest_path),
            call(data=project_data.readme_report.render_html.return_value,
                 filepath=mock_settings.readme_html_dest_path),
            call(data=json.dumps({"id": "42"}),
                 filepath=mock_settings.job_data_dest_path),
        ])

    @patch('lando_util.organize_project.organizer.os')
    @patch('lando_util.organize_project.organizer.shutil')
    @patch('lando_util.organize_project.organizer.ProjectData')
    @patch('lando_util.organize_project.organizer.write_data_to_file')
    @patch('lando_util.organize_project.organizer.zipfile')
    def test_run_zipped(self, mock_zipfile, mock_write_data_to_file, mock_project_data, mock_shutil, mock_os):
        mock_settings = Mock()
        mock_settings.workflow_type = 'zipped'
        mock_settings.bespin_job_id = '42'
        mock_settings.bespin_workflow_started = '2019-02-07T12:30'
        mock_settings.bespin_workflow_finished = '2019-02-09T12:45'
        mock_settings.bespin_workflow_elapsed_minutes = '120'
        mock_settings.workflow_path = '/workflow/workflow.zip'
        mock_settings.workflow_dest_path = '/workflow/outdir'
        mock_settings.logs_dir = '/results/docs/logs/'
        mock_settings.additional_log_files = ['/tmp/extra/usage-report.txt', '/data/log2.txt']
        mock_settings.job_data = {}
        mock_project_data.return_value = Mock(
            methods_template='#Markdown',
            job_data={
                'id': '42',
            }
        )
        mock_os.path = os.path

        organizer = Organizer(mock_settings)
        organizer.run()

        mock_os.makedirs.assert_has_calls([
            call(exist_ok=True, name=mock_settings.docs_dir),
            call(exist_ok=True, name=mock_settings.scripts_dir),
            call(exist_ok=True, name=mock_settings.logs_dir),
        ])
        mock_shutil.copy.assert_has_calls([
            call(mock_settings.job_order_path, mock_settings.job_order_dest_path),
            call(mock_settings.bespin_workflow_stdout_path, mock_settings.bespin_workflow_stdout_dest_path),
            call(mock_settings.bespin_workflow_stderr_path, mock_settings.bespin_workflow_stderr_dest_path),
            call('/tmp/extra/usage-report.txt', '/results/docs/logs/usage-report.txt'),
            call('/data/log2.txt', '/results/docs/logs/log2.txt'),
        ])
        project_data = mock_project_data.return_value
        mock_write_data_to_file.assert_has_calls([
            call(data=project_data.readme_report.render_markdown.return_value,
                 filepath=mock_settings.readme_md_dest_path),
            call(data=project_data.readme_report.render_html.return_value,
                 filepath=mock_settings.readme_html_dest_path),
            call(data=json.dumps({"id": "42"}),
                 filepath=mock_settings.job_data_dest_path),
        ])
        mock_zipfile.ZipFile.assert_called_with('/workflow/workflow.zip')
        mock_zipfile.ZipFile.return_value.__enter__.return_value.extractall.assert_called_with('/workflow/outdir')
