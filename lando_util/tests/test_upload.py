from unittest import TestCase
from unittest.mock import patch, Mock, call, mock_open
from lando_util.upload import Settings, UploadUtil, main, UploadedFilesInfo, DukeDSActivity
import json


SAMPLE_JOB_OUTPUT = {
    "align_log": [
        {
            "class": "File",
            "checksum": "sha1$0e724dda4c96d901af1ecd53d0cd5882d6b1a814",
            "location": "/tmp/align_log.txt",
            "size": 900,
            "secondaryFiles": [
                {
                    "class": "File",
                    "checksum": "sha1$6ec2f899946f8091693ce65cc6323958695dec21",
                    "location": "/tmp/align_log.idx",
                    "size": 123
                }
            ]
        }
    ],
    "aligned_read": {
        "class": "File",
        "checksum": "sha1$0e724dda4c96d901af1ecd53d0cd5882d6b1a814",
        "location": "/tmp/aligned_read.txt",
        "size": 1010123,
        "secondaryFiles": [
            {
                "class": "File",
                "checksum": "sha1$6ec2f899946f8091693ce65cc6323958695dec20",
                "location": "/tmp/aligned_read.idx",
                "size": 6613916
            }
        ]
    },
    "trim_reports": [
        [
            {
                "class": "File",
                "checksum": "sha1$0e724dda4c96d901af1ecd53d0cd5882d6b1a815",
                "location": "/tmp/trim_report.txt",
                "size": 44,
            }
        ]
    ],
    "bams_markduplicates_dir": {
        "class": "Directory",
        "basename": "bams-markduplicates",
        "location": "file:///work/data_for_job_49/working/results/bams-markduplicates",
        "listing": [
            {
                "checksum": "sha1$878d31004d7867b9ded64426657519a28b7ce46b",
                "location": "file:///work/data_for_job_49/working/results/bams-markduplicates/SA03505-dedup.bam",
                "secondaryFiles": [
                    {
                        "checksum": "sha1$2144e6c9778fa3564e4b1a4069cee3a7f3ef9d1b",
                        "location": "file:///work/data_for_job_49/working/results/bams-markduplicates/SA03505-dedup.bai",
                        "class": "File",
                        "size": 6218232
                    }
                ],
                "class": "File",
                "size": 5570967966
            },
            {
                "checksum": "sha1$59697e90052dc258b6887e8c84eb42c2f5ae0842",
                "location": "file:///work/data_for_job_49/working/results/bams-markduplicates/SA03567-dedup.bam",
                "secondaryFiles": [
                    {
                        "checksum": "sha1$9486797d5dd4c2c757b853bc21d64f790988b207",
                        "location": "file:///work/data_for_job_49/working/results/bams-markduplicates/SA03567-dedup.bai",
                        "class": "File",
                        "size": 6309968
                    }
                ],
                "class": "File",
                "size": 7253903222
            },
        ]
    }
}


class TestSettings(TestCase):
    @patch('lando_util.upload.json')
    def test_constructor_minimal_data(self, mock_json):
        mock_json.load.return_value = {
            "destination": "myproject",
            "readme_file_path": "results/docs/README.md",
            "paths": ["/data/results"],
            "share": {
                "dds_user_ids": ["123","456"]
            },
            "activity": {
                "name": "myactivity",
                "description": "mydesc",
                "started_on": "2019-03-01 12:30",
                "ended_on": "2019-03-01 12:35",
                "input_file_version_ids": [
                    "abd123",
                ],
                "output_file_paths": [
                    "/data/results/output.txt"
                ],
                "workflow_output_json_path": "bespin-workflow-output.json"
            }
        }
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.destination, "myproject")
        self.assertEqual(settings.paths, ["/data/results"])
        self.assertEqual(settings.share_dds_user_ids, ["123","456"])
        self.assertEqual(settings.share_auth_role, "project_admin")
        self.assertEqual(settings.share_user_message, "Bespin job results.")
        self.assertEqual(settings.activity_settings.name, "myactivity")
        self.assertEqual(settings.activity_settings.description, "mydesc")
        self.assertEqual(settings.activity_settings.started_on, "2019-03-01 12:30")
        self.assertEqual(settings.activity_settings.ended_on, "2019-03-01 12:35")
        self.assertEqual(settings.activity_settings.input_file_version_ids, ["abd123"])
        self.assertEqual(settings.activity_settings.workflow_output_json_path, "bespin-workflow-output.json")

    @patch('lando_util.upload.json')
    def test_constructor_optional_values(self, mock_json):
        mock_json.load.return_value = {
            "destination": "myproject",
            "readme_file_path": "results/docs/README.md",
            "paths": ["/data/results"],
            "share": {
                "dds_user_ids": ["123","456"],
                "auth_role": "project_downloader",
                "user_message": "Other stuff"
            },
            "activity": {
                "name": "myactivity",
                "description": "mydesc",
                "started_on": "2019-03-01 12:30",
                "ended_on": "2019-03-01 12:35",
                "input_file_version_ids": [
                    "abd123",
                ],
                "workflow_output_json_path": "bespin-workflow-output.json"
            }
        }
        mock_cmdfile = Mock()
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.share_auth_role, "project_downloader")
        self.assertEqual(settings.share_user_message, "Other stuff")


@patch('lando_util.upload.Settings')
@patch('lando_util.upload.DukeDSClient')
class TestUploadUtil(TestCase):
    def test_get_or_create_project_creates_project(self, mock_duke_ds_client, mock_settings):
        mock_settings.return_value.destination = 'myproject'
        mock_duke_ds_client.return_value.get_projects.return_value = []
        util = UploadUtil(Mock())
        project = util.get_or_create_project()
        self.assertEqual(project, util.dds_client.create_project.return_value)
        util.dds_client.create_project.assert_called_with('myproject', description='myproject')

    def test_get_or_create_project_finds_project(self, mock_duke_ds_client, mock_settings):
        mock_settings.return_value.destination = 'myproject'
        mock_project = Mock()
        mock_project.name = 'myproject'
        mock_duke_ds_client.return_value.get_projects.return_value = [
            mock_project
        ]
        util = UploadUtil(Mock())
        project = util.get_or_create_project()
        self.assertEqual(project, mock_project)
        util.dds_client.create_project.assert_not_called()

    @patch('lando_util.upload.ProjectUpload')
    @patch('lando_util.upload.ProjectNameOrId')
    @patch('lando_util.upload.UploadedFilesInfo')
    @patch('lando_util.upload.click')
    def test_upload_files(self, mock_click, mock_uploaded_files_info, mock_project_name_or_id, mock_project_upload,
                          mock_duke_ds_client,
                          mock_settings):
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project.id = '123456'
        mock_project_upload.return_value.needs_to_upload.return_value = True
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 2 files to upload.'
        uploaded_files_info = util.upload_files(project=mock_project)
        mock_project_upload.assert_called_with(
            mock_duke_ds_client.return_value.dds_connection.config,
            mock_project_name_or_id.create_from_project_id.return_value,
            mock_settings.return_value.paths
        )
        mock_project_name_or_id.create_from_project_id.assert_called_with('123456')
        mock_click.echo.assert_has_calls([
            call('There are 2 files to upload.'),
            call('Uploading')
        ])
        self.assertEqual(uploaded_files_info, mock_uploaded_files_info.return_value)
        mock_uploaded_files_info.assert_called_with(mock_project_upload.return_value.local_project)

    @patch('lando_util.upload.ProjectUpload')
    @patch('lando_util.upload.click')
    def test_upload_files_no_files_found(self, mock_click, mock_project_upload, mock_duke_ds_client, mock_settings):
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 0 files to upload.'
        mock_project_upload.return_value.needs_to_upload.return_value = False
        util.upload_files(project=mock_project)
        mock_click.echo.assert_called_with('There are 0 files to upload.')

    @patch('lando_util.upload.DukeDSActivity')
    def test_create_provenance_activity(self, mock_duke_ds_activity, mock_duke_ds_client, mock_settings):
        mock_uploaded_files_info = Mock()
        util = UploadUtil(Mock())
        util.create_provenance_activity(mock_uploaded_files_info)
        mock_duke_ds_activity.assert_called_with(util.dds_client, util.settings, mock_uploaded_files_info)
        mock_duke_ds_activity.return_value.create.assert_called_with()

    @patch('lando_util.upload.RemoteStore')
    @patch('lando_util.upload.D4S2Project')
    def test_share_project(self, mock_d4s2_project, mock_remote_store, mock_duke_ds_client, mock_settings):
        mock_settings.return_value.share_dds_user_ids = ['444', '555']
        mock_settings.return_value.share_auth_role = 'somerole'
        mock_settings.return_value.share_user_message = 'someMessage'
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project.id = '111'

        util.share_project(mock_project)

        mock_remote_store.return_value.fetch_remote_project_by_id.assert_called_with('111')
        mock_remote_project = mock_remote_store.return_value.fetch_remote_project_by_id.return_value
        mock_remote_user = mock_remote_store.return_value.fetch_user.return_value
        mock_d4s2_project.return_value.share.assert_called_with(
            mock_remote_project,
            mock_remote_user,
            auth_role='somerole',
            force_send=True,
            user_message='someMessage'
        )
        mock_remote_store.return_value.fetch_user.assert_has_calls([
            call('444'),
            call('555'),
        ])

    def test_create_annotate_project_details_script(self, mock_duke_ds_client, mock_settings):
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project.id = '888'
        mock_readme_file = Mock()
        mock_readme_file.id = '999'
        mock_project.get_child_for_path.return_value = mock_readme_file
        mock_outfile = Mock()
        util.create_annotate_project_details_script(mock_project, mock_outfile)
        mock_outfile.write.assert_called_with('kubectl annotate pod $MY_POD_NAME project_id=888 readme_file_id=999')


class TestMain(TestCase):
    @patch('lando_util.upload.UploadUtil')
    def test_main(self, mock_upload_util):
        mock_cmdfile = Mock()
        mock_outfile = Mock()

        main.callback(mock_cmdfile, mock_outfile)

        mock_upload_util.assert_called_with(mock_cmdfile)
        upload_util = mock_upload_util.return_value
        upload_util.get_or_create_project.assert_called_with()
        mock_project = upload_util.get_or_create_project.return_value
        upload_util.create_provenance_activity.assert_called_with(
            upload_util.upload_files.return_value
        )
        upload_util.share_project.assert_called_with(mock_project)
        upload_util.create_annotate_project_details_script.assert_called_with(
            mock_project, mock_outfile)


class TestUploadedFilesInfo(TestCase):
    """
    Copied from https://github.com/Duke-GCB/lando/blob/76f981ebff4ae0abbabbc4461308e9e5ea0bc830/lando/worker/tests/
    test_provenance.py#L45
    """
    def test_file_id_lookup(self):
        mock_file1 = Mock(kind='dds-file', remote_id='123', path='/tmp/data.txt')
        mock_file2 = Mock(kind='dds-file', remote_id='124', path='/tmp/data2.txt')
        mock_folder = Mock(kind='dds-folder', children=[mock_file2])
        mock_project = Mock(kind='dds-project', children=[mock_file1, mock_folder])
        project_info = UploadedFilesInfo(project=mock_project)
        expected_dictionary = {'/tmp/data.txt': '123', '/tmp/data2.txt': '124'}
        self.assertEqual(expected_dictionary, project_info.file_id_lookup)


class TestDukeDSActivity(TestCase):
    def setUp(self):
        self.mock_dds_client = Mock()
        self.mock_dds_client.get_file_by_id.return_value = Mock(current_version={"id": "999"})
        self.mock_data_service = self.mock_dds_client.dds_connection.data_service
        mock_activity_response = Mock()
        mock_activity_response.json.return_value = {"id": "111"}
        mock_data_service = self.mock_dds_client.dds_connection.data_service
        mock_data_service.create_activity.return_value = mock_activity_response
        mock_activity_settings = Mock(
            description="mydescription",
            started_on="2019-01-01 12:30",
            ended_on="2019-01-01 12:35",
            input_file_version_ids=["222", "333", "444"],
            workflow_output_json_path="/data/workflow_output.json",
        )
        self.mock_workflow_output_str = json.dumps({
            "one": {
                "class": "File",
                "location": "/data/one.txt",
            },
            "two": {
                "class": "File",
                "location": "/data/two.txt",
            },
        })
        mock_activity_settings.name = "myactivity"
        self.mock_settings = Mock(activity_settings=mock_activity_settings)
        self.mock_project_info = Mock(file_id_lookup={
            "/data/one.txt": "678",
            "/data/two.txt": "890",
        })



    @patch('lando_util.upload.click')
    def test_create_echos_progress(self, mock_click):
        with patch("builtins.open", mock_open(read_data=self.mock_workflow_output_str)) as mock_file:
            activity = DukeDSActivity(self.mock_dds_client, self.mock_settings, self.mock_project_info)
            activity.create()

        mock_click.echo.assert_has_calls([
            call('Creating activity myactivity.'),
            call('Attaching 3 used relations.'),
            call('Attaching 2 generated relations.'),
        ])
        mock_file.assert_called_with('/data/workflow_output.json', 'r')

    @patch('lando_util.upload.click')
    def test_create_updates_dukeds(self, mock_click):
        with patch("builtins.open", mock_open(read_data=self.mock_workflow_output_str)) as mock_file:
            activity = DukeDSActivity(self.mock_dds_client, self.mock_settings, self.mock_project_info)
            activity.create()

        self.mock_data_service.create_activity.assert_called_with(
            'myactivity', 'mydescription', '2019-01-01 12:30', '2019-01-01 12:35')
        self.mock_data_service.create_used_relation.assert_has_calls([
            call('111', 'dds-file', '222'),
            call('111', 'dds-file', '333'),
            call('111', 'dds-file', '444')
        ])

        self.mock_data_service.create_was_generated_by_relation.assert_has_calls([
            call('111', 'dds-file', '999'), call('111', 'dds-file', '999')
        ])

        self.mock_dds_client.get_file_by_id.assert_has_calls([
            call('678'), call('890')
        ])
