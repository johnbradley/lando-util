import os
import json
from unittest import TestCase
from unittest.mock import patch, Mock, call
from lando_util.download import get_stage_items, download_files, write_downloaded_metadata, main


class TestDownloadFunctions(TestCase):
    @patch('lando_util.download.json')
    def test_get_stage_items(self, mock_json):
        mock_json.load.return_value = {
            "items": [
                {"type": "DukeDS", "source": "123456", "dest": "/data/file1.dat"},
                {"type": "url", "source": "someurl", "dest": "/data/file2.dat"},
                {"type": "write", "source": "MYDATA:12", "dest": "/data/file3.dat"},
            ]
        }
        mock_cmdfile = Mock()

        result = get_stage_items(mock_cmdfile)

        mock_json.load.assert_called_with(mock_cmdfile)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ("DukeDS", "123456", "/data/file1.dat"))
        self.assertEqual(result[1], ("url", "someurl", "/data/file2.dat"))
        self.assertEqual(result[2], ("write", "MYDATA:12", "/data/file3.dat"))

    @patch("lando_util.download.os")
    @patch("lando_util.download.urllib")
    @patch("builtins.open")
    @patch("lando_util.download.click")
    def test_download_files(self, mock_click, mock_open, mock_urllib, mock_os):
        mock_os.path.dirname = lambda x: os.path.dirname(x)
        mock_dds_client = Mock()
        mock_dds_client.get_file_by_id.return_value = Mock(_data_dict={"current_version": {"id": "999"}})
        stage_items = [
            ("DukeDS", "123456", "/data/file1.dat"),
            ("url", "someurl", "/data/file2.dat"),
            ("write", "MYDATA:12", "/data/file3.dat"),
        ]

        result = download_files(mock_dds_client, stage_items)

        mock_click.echo.assert_has_calls([
            call("Staging 3 items."),
            call("Downloading DukeDS file 123456 to /data/file1.dat."),
            call("Downloading URL someurl to /data/file2.dat."),
            call("Writing file /data/file3.dat."),
            call("Staging complete."),
        ])
        mock_os.makedirs.assert_has_calls([
            call("/data", exist_ok=True),
            call("/data", exist_ok=True),
            call("/data", exist_ok=True),
        ])

        mock_dds_client.get_file_by_id.assert_called_with(file_id="123456")
        mock_dds_client.get_file_by_id.return_value.download_to_path.assert_called_with('/data/file1.dat')

        mock_urllib.request.urlretrieve.assert_called_with("someurl", "/data/file2.dat")

        mock_open.assert_called_with('/data/file3.dat', 'w')
        mock_open.return_value.__enter__.return_value.write.assert_called_with('MYDATA:12')
        self.assertEqual(result, [{'current_version': {'id': '999'}}])

    @patch("lando_util.download.click")
    def test_write_downloaded_metadata_writes_json_file(self, mock_click):
        mock_outfile = Mock()
        mock_outfile.name = "myoutfile.json"
        downloaded_metadata_items = [
            {'current_version': {'id': '111'}},
            {'current_version': {'id': '222'}},
        ]
        write_downloaded_metadata(mock_outfile, downloaded_metadata_items)
        mock_click.echo.assert_called_with("Writing 2 metadata items to myoutfile.json.")
        mock_outfile.write.assert_called_with(json.dumps({
            "items": [
                {'current_version': {'id': '111'}},
                {'current_version': {'id': '222'}},
            ]
        }))

    @patch('lando_util.download.DukeDSClient')
    @patch('lando_util.download.get_stage_items')
    @patch('lando_util.download.download_files')
    @patch('lando_util.download.write_downloaded_metadata')
    def test_main_without_downloaded_metadata_file(self, mock_write_downloaded_metadata, mock_download_files,
                                                   mock_get_stage_items, mock_duke_ds_client):
        mock_cmdfile = Mock()

        main.callback(mock_cmdfile, None)

        mock_get_stage_items.assert_called_with(mock_cmdfile)
        mock_download_files.assert_called_with(mock_duke_ds_client.return_value, mock_get_stage_items.return_value)
        mock_write_downloaded_metadata.assert_not_called()

    @patch('lando_util.download.DukeDSClient')
    @patch('lando_util.download.get_stage_items')
    @patch('lando_util.download.download_files')
    @patch('lando_util.download.write_downloaded_metadata')
    def test_main_with_downloaded_metadata_file(self, mock_write_downloaded_metadata, mock_download_files,
                                                   mock_get_stage_items, mock_duke_ds_client):
        mock_cmdfile = Mock()
        mock_metadata_file = Mock()

        main.callback(mock_cmdfile, mock_metadata_file)

        mock_get_stage_items.assert_called_with(mock_cmdfile)
        mock_download_files.assert_called_with(mock_duke_ds_client.return_value, mock_get_stage_items.return_value)
        mock_write_downloaded_metadata.assert_called_with(mock_metadata_file, mock_download_files.return_value)
