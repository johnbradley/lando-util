import os
from unittest import TestCase
from unittest.mock import patch, Mock, call
from lando_util.upload import UploadList, create_annotate_project_details_script, share_project, upload_files


class TestUploadList(TestCase):
    @patch('lando_util.upload.json')
    def test_constructor_minimal_data(self, mock_json):
        mock_json.load.return_value = {
            "destination": "myproject",
            "readme_file_path": "results/docs/README.md",
            "paths": ["/data/results"],
            "share": {
                "dds_user_ids": ["123","456"]
            }
        }
        mock_cmdfile = Mock()
        upload_list = UploadList(mock_cmdfile)
        self.assertEqual(upload_list.destination, "myproject")
        self.assertEqual(upload_list.paths, ["/data/results"])
        self.assertEqual(upload_list.share_dds_user_ids, ["123","456"])
        self.assertEqual(upload_list.share_auth_role, "project_admin")
        self.assertEqual(upload_list.share_user_message, "Bespin job results.")

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
        }
        mock_cmdfile = Mock()
        upload_list = UploadList(mock_cmdfile)
        self.assertEqual(upload_list.share_auth_role, "project_downloader")
        self.assertEqual(upload_list.share_user_message, "Other stuff")


class TestUploadFunctions(TestCase):
    def test_create_annotate_project_details_script(self):
        mock_outfile = Mock()
        create_annotate_project_details_script(project_id='123', readme_file_id='456', outfile=mock_outfile)
        mock_outfile.write.assert_called_with('kubectl annotate pod $MY_POD_NAME project_id=123 readme_file_id=456')

    @patch('lando_util.upload.RemoteStore')
    @patch('lando_util.upload.D4S2Project')
    def test_share_project(self, mock_d4s2_project, mock_remote_store):
        mock_dds_client = Mock()
        share_project_id = '123'
        mock_upload_list = Mock(
            destination="myProject", paths=["/data/results"],
            share_auth_role='project_admin', share_user_message='Hey')
        mock_upload_list.share_dds_user_ids = ['456', '789']
        share_project(mock_dds_client, share_project_id, mock_upload_list)

        mock_remote_store.return_value.fetch_remote_project_by_id.assert_called_with('123')
        mock_remote_project = mock_remote_store.return_value.fetch_remote_project_by_id.return_value
        mock_remote_user = mock_remote_store.return_value.fetch_user.return_value
        mock_remote_store.return_value.fetch_user.assert_has_calls([
            call("456"), call("789")
        ])

        mock_d4s2_project.return_value.share.assert_has_calls([
            call(mock_remote_project, mock_remote_user, auth_role='project_admin', force_send=True, user_message='Hey'),
            call(mock_remote_project, mock_remote_user, auth_role='project_admin', force_send=True, user_message='Hey'),
        ])

    @patch("lando_util.upload.ProjectUpload")
    @patch("lando_util.upload.create_annotate_project_details_script")
    @patch("lando_util.upload.share_project")
    @patch("lando_util.upload.click")
    def test_upload_files(self, mock_click, mock_share_project, mock_create_annotate_project_details_scripts,
                          mock_project_upload):
        mock_dds_client = Mock()
        mock_upload_list = Mock(
            destination="myProject", paths=["/data/results"],
            share_auth_role='project_admin', share_user_message='Hey')
        mock_upload_list.share_dds_user_ids = ['456', '789']
        mock_upload_list.readme_file_path = 'somepath.md'
        mock_outfile = Mock()
        mock_project = Mock()
        mock_project.id = '123'
        mock_readme_file = Mock()
        mock_readme_file.id = '456'
        mock_project.get_child_for_path.return_value = mock_readme_file
        mock_dds_client.create_project.return_value = mock_project
        mock_project_upload.return_value.needs_to_upload.return_value = True
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 2 files to upload.'

        upload_files(mock_dds_client, mock_upload_list, mock_outfile)

        mock_click.echo.assert_has_calls([
            call('Uploading 1 paths to myProject.'),
            call('There are 2 files to upload.'),
            call('Uploading')])
        mock_dds_client.create_project.assert_called_with('myProject', description='myProject')
        mock_create_annotate_project_details_scripts.assert_called_with('123', '456', mock_outfile)
        mock_share_project.assert_called_with(mock_dds_client, '123', mock_upload_list)
        mock_project.get_child_for_path.assert_called_with('somepath.md')

    @patch("lando_util.upload.ProjectUpload")
    @patch("lando_util.upload.create_annotate_project_details_script")
    @patch("lando_util.upload.share_project")
    @patch("lando_util.upload.click")
    def test_upload_files_no_data(self, mock_click, mock_share_project, mock_create_annotate_project_details_script,
                                  mock_project_upload):
        mock_dds_client = Mock()
        mock_upload_list = Mock(
            destination="myProject", paths=["/data/results"],
            share_auth_role='project_admin', share_user_message='Hey')
        mock_upload_list.share_dds_user_ids = ['456', '789']
        mock_outfile = Mock()
        mock_project = Mock()
        mock_project.id = '123'
        mock_dds_client.create_project.return_value = mock_project
        mock_project_upload.return_value.needs_to_upload.return_value = False
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 0 files to upload.'

        with self.assertRaises(ValueError) as raised_exception:
            upload_files(mock_dds_client, mock_upload_list, mock_outfile)
        self.assertEqual(str(raised_exception.exception), 'Error: No files or folders found to upload.')

        mock_click.echo.assert_has_calls([
            call('Uploading 1 paths to myProject.'),
            call('There are 0 files to upload.')])
        mock_dds_client.create_project.assert_called_with('myProject', description='myProject')
        mock_dds_client.create_project.return_value.delete.assert_called_with()
        mock_create_annotate_project_details_script.assert_not_called()
        mock_share_project.assert_not_called()
