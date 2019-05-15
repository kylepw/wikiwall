from click.testing import CliRunner
import unittest
import unittest.mock as mock
import wikiwall
from wikiwall import cli


class CliTest(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

        self.patcher_info = mock.patch.object(wikiwall.logger, 'info')
        self.mock_info = self.patcher_info.start()

        # Mock out functions called from cli().
        self.patcher_config_logger = mock.patch('wikiwall.config_logger')
        self.mock_config_logger = self.patcher_config_logger.start()

        self.patcher_clean_dls = mock.patch('wikiwall._clean_dls')
        self.mock_clean_dls = self.patcher_clean_dls.start()

        self.patcher_run_appscript = mock.patch('wikiwall._run_appscript')
        self.mock_run_appscript = self.patcher_run_appscript.start()

        self.patcher_download_img = mock.patch('wikiwall.download_img')
        self.mock_download_img = self.patcher_download_img.start()

        self.patcher_get_random = mock.patch('wikiwall.get_random')
        self.mock_get_random = self.patcher_get_random.start()

        self.patcher_scrape_urls = mock.patch('wikiwall.scrape_urls')
        self.mock_scrape_urls = self.patcher_scrape_urls.start()

        self.patcher_datadir = mock.patch('wikiwall.data_dir', return_value='/tmp')
        self.mock_datadir = self.patcher_datadir.start()

        self.patcher_time = mock.patch('wikiwall.time')
        self.mock_time = self.patcher_time.start()

        self.patcher_sys = mock.patch('wikiwall.sys')
        self.mock_sys = self.patcher_sys.start()

        self.patcher_db = mock.patch(
            'wikiwall.DownloadDatabase',
            return_value=mock.Mock(
                __enter__=mock.Mock(
                    return_value=mock.Mock(
                        is_duplicate=mock.Mock(return_value=False),
                        add=mock.Mock()
                    )
                ),
                __exit__=mock.Mock(return_value=None),
            )
        )
        self.mock_db = self.patcher_db.start()


    def tearDown(self):
        self.patcher_info.stop()
        self.patcher_config_logger.stop()
        self.patcher_clean_dls.stop()
        self.patcher_run_appscript.stop()
        self.patcher_download_img.stop()
        self.patcher_get_random.stop()
        self.patcher_scrape_urls.stop()
        self.patcher_datadir.stop()
        self.patcher_time.stop()
        self.patcher_db.stop()
        self.patcher_sys.stop()

    def test_debug_on_message(self):
        result = self.runner.invoke(cli, ['--debug'])
        self.assertIn('Debug mode is on.', result.output)

    def test_dest_with_value_given(self):
        dest = '/tmp'
        self.runner.invoke(cli, ['--debug', f'--dest={dest}'])

        self.mock_info.assert_any_call('Destination set to %s', dest)

    def test_no_limit(self):
        self.runner.invoke(cli, ['--limit', '-1'])

        self.mock_info.assert_any_call('No download limit set. Skipping cleaning.')

    def test_limit_set_to_12(self):
        limit = 12

        self.runner.invoke(cli, ['--limit', f'{limit}'])

        self.mock_info.assert_any_call('Download limit set to %s.', limit)

    def test_message_on_random_exception_in_cli_body(self):
        with mock.patch('wikiwall.get_random', side_effect=ValueError):
            result = self.runner.invoke(cli, ['--limit', '2'])
        self.assertIn('Something went wrong. Check the logs.', result.output)


class ShowSubcommandTest(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

        self.patcher_runapp = mock.patch('wikiwall._run_appscript')
        self.mock_runapp = self.patcher_runapp.start()

    def tearDown(self):
        self.patcher_runapp.stop()

    def test_cli_code_doesnt_execute_if_show_subcommand_passed(self):

        with mock.patch('wikiwall.get_random') as mock_get_random:
            self.runner.invoke(cli, ['show'])
        mock_get_random.assert_not_called()

    def test_show_subcommand_runs_applescript(self):

        self.runner.invoke(cli, ['show'])
        self.mock_runapp.assert_called()
