from click.testing import CliRunner
import unittest
import unittest.mock as mock
from wikiwall import cli, logger


class CliTest(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

        self.patcher_info = mock.patch.object(logger, 'info')
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

    def tearDown(self):
        self.patcher_info.stop()
        self.patcher_config_logger.stop()
        self.patcher_clean_dls.stop()
        self.patcher_run_appscript.stop()
        self.patcher_download_img.stop()
        self.patcher_get_random.stop()
        self.patcher_scrape_urls.stop()

    def test_debug_on_message(self):
        result = self.runner.invoke(cli, ['--debug'])
        self.assertIn('Debug mode is on.', result.output)

    def test_dest_with_value_given(self):
        dest = '/tmp'
        self.runner.invoke(cli, [f'--dest={dest}'])

        self.mock_info.assert_any_call('Destination set to %s', dest)

    def test_no_limit(self):
        self.runner.invoke(cli, ['--limit', '-1'])

        self.mock_info.assert_any_call(
            'No download limit set. Skipping cleaning.'
        )

    def test_limit_set_to_12(self):
        limit = 12
        self.runner.invoke(cli, [f'--limit={limit}'])

        self.mock_info.assert_any_call('Download limit set to %s.', limit)

    def test_show_subcommand(self):
        pass
