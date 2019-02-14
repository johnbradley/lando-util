from unittest import TestCase
from unittest.mock import patch, Mock, call
from lando_util.upload import Settings, NothingToUploadException, UploadUtil, main


class TestSettings(TestCase):
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
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.destination, "myproject")
        self.assertEqual(settings.paths, ["/data/results"])
        self.assertEqual(settings.share_dds_user_ids, ["123","456"])
        self.assertEqual(settings.share_auth_role, "project_admin")
        self.assertEqual(settings.share_user_message, "Bespin job results.")

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
        settings = Settings(mock_cmdfile)
        self.assertEqual(settings.share_auth_role, "project_downloader")
        self.assertEqual(settings.share_user_message, "Other stuff")


@patch('lando_util.upload.Settings')
@patch('lando_util.upload.DukeDSClient')
class TestUploadUtil(TestCase):
    def test_create_project(self, mock_duke_ds_client, mock_settings):
        mock_settings.return_value.destination = 'myproject'
        util = UploadUtil(Mock())
        project = util.create_project()
        self.assertEqual(project, util.dds_client.create_project.return_value)
        util.dds_client.create_project.assert_called_with('myproject', description='myproject')

    @patch('lando_util.upload.ProjectUpload')
    @patch('lando_util.upload.ProjectNameOrId')
    @patch('lando_util.upload.click')
    def test_upload_files(self, mock_click, mock_project_name_or_id, mock_project_upload, mock_duke_ds_client,
                          mock_settings):
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project.id = '123456'
        mock_project_upload.return_value.needs_to_upload.return_value = True
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 2 files to upload.'
        util.upload_files(project=mock_project)
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

    @patch('lando_util.upload.ProjectUpload')
    @patch('lando_util.upload.click')
    def test_upload_files_no_files_found(self, mock_click, mock_project_upload, mock_duke_ds_client, mock_settings):
        util = UploadUtil(Mock())
        mock_project = Mock()
        mock_project_upload.return_value.get_differences_summary.return_value = 'There are 0 files to upload.'
        mock_project_upload.return_value.needs_to_upload.return_value = False
        with self.assertRaises(NothingToUploadException):
            util.upload_files(project=mock_project)
        mock_click.echo.assert_called_with('There are 0 files to upload.')

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
        mock_upload_util.return_value.create_project.assert_called_with()
        mock_project = mock_upload_util.return_value.create_project.return_value
        mock_upload_util.return_value.share_project.assert_called_with(mock_project)
        mock_upload_util.return_value.create_annotate_project_details_script.assert_called_with(
            mock_project, mock_outfile)

    @patch('lando_util.upload.UploadUtil')
    def test_main_nothing_to_upload(self, mock_upload_util):
        mock_cmdfile = Mock()
        mock_outfile = Mock()
        mock_upload_util.return_value.upload_files.side_effect = NothingToUploadException("Nothing to upload")

        with self.assertRaises(NothingToUploadException):
            main.callback(mock_cmdfile, mock_outfile)
        mock_upload_util.return_value.create_project.return_value.delete.assert_called_with()
