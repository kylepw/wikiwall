import os
import os.path
import requests
from requests.exceptions import HTTPError, InvalidURL, MissingSchema
import tempfile
import unittest
import unittest.mock as mock
import wikiwall
from wikiwall import (
    config_logger,
    data_dir,
    _clean_dls,
    _run_appscript,
    download_img,
    get_random,
    scrape_urls,
)


class ConfigLoggerTest(unittest.TestCase):

    def setUp(self):
        self.patcher_logging = mock.patch('wikiwall.logging')
        self.mock_logging = self.patcher_logging.start()

        self.patcher_rotate = mock.patch('wikiwall.RotatingFileHandler')
        self.mock_rotate = self.patcher_rotate.start()

        self.patcher_getcwd = mock.patch(
            'wikiwall.os.getcwd',
            return_value='/Users/mock',
            autospec=True
        )
        self.mock_getcwd = self.patcher_getcwd.start()

    def tearDown(self):
        self.patcher_logging.stop()
        self.patcher_rotate.stop()
        self.patcher_getcwd.stop()

    def test_debug_is_true(self):
        with mock.patch.object(wikiwall.logging, 'StreamHandler') as mock_sh:
            config_logger(debug=True)
        mock_sh.assert_called()

    def test_debug_is_None(self):
        with mock.patch.object(wikiwall.logging, 'StreamHandler') as mock_sh:
            config_logger(debug=None)
        mock_sh.assert_not_called()

    def test_path_is_None(self):
        config_logger(debug=None, path=None)
        self.mock_getcwd.assert_called_once()

    def test_path_is_not_None(self):
        config_logger(debug=None, path='/mock/path')
        self.mock_getcwd.assert_not_called()


class DataDirTest(unittest.TestCase):

    def setUp(self):
        self.patcher_makedirs = mock.patch(
            'wikiwall.os.makedirs',
            autospec=True,
        )
        self.mock_makedirs = self.patcher_makedirs.start()

        self.patcher_expanduser = mock.patch(
            'wikiwall.os.path.expanduser',
            return_value='/Users/mock',
            autospec=True
        )
        self.mock_expanduser = self.patcher_expanduser.start()

    def tearDown(self):
        self.patcher_makedirs.stop()
        self.patcher_expanduser.stop()

    @mock.patch.dict(os.environ, {'XDG_DATA_HOME': '/tmp'})
    def test_xdg_data_home_env_variable_exists(self):
        self.assertEqual(data_dir(), '/tmp/wikiwall')

    @mock.patch.dict(os.environ, {})
    def test_xdg_data_home_env_variables_doesnt_exist(self):
        self.assertEqual(
            data_dir(),
            os.path.join(
                self.mock_expanduser.return_value,
                '.local/share/wikiwall'
            )
        )


class GetRandomTest(unittest.TestCase):

    def test_blank_parameter(self):
        with self.assertRaises(TypeError):
            get_random()

    def test_non_iterable_argument(self):
        with self.assertRaises(TypeError):
            get_random(45)

    def test_returns_result_with_k_num_of_items(self):
        values, k = ['a', 'b', 'c', 'd', 'e', 'f'], 4
        self.assertEqual(len(get_random(values, k)), k)

    def test_item_returned_are_from_original_iterable(self):
        values, k = ['a', 3.45, 'jazz', (1, 2), ['z' 'g'], 'gah', 3], 4
        for val in get_random(values, k):
            self.assertIn(val, values)

    def test_for_warning_if_k_is_greater_than_size_of_iterable(self):
        values, k = ['a', 'b', 'c', 'd', 'e', 'f'], 10

        with mock.patch('wikiwall.logger') as mock_logger:
            get_random(values, k)
        mock_logger.warning.assert_called_with(
            'Size of iterator (%s) is less than k (%s)',
            len(values), k
        )


class ScrapeUrlsTest(unittest.TestCase):

    def setUp(self):
        self.patcher_get = mock.patch('wikiwall.requests.get', autospec=True)
        self.mock_get = self.patcher_get.start()

    def tearDown(self):
        self.patcher_get.stop()

    def get_resp(
        self,
        status_code=200,
        content='<html></html>',
        raise_for_status=None
    ):
        ''' Returns a mock requests Response object.'''
        mock_resp = mock.Mock(spec=requests.models.Response)
        mock_resp.status_code = status_code
        mock_resp.content = content

        # mock raise_for_status call w/optional error
        if raise_for_status:
            mock_resp.raise_for_status = mock.Mock(
                side_effect=raise_for_status
            )

        return mock_resp

    def test_missing_src_url(self):
        with self.assertRaises(TypeError):
            scrape_urls()

    def test_invalid_src_url(self):
        self.mock_get.side_effect = MissingSchema

        with self.assertRaises(MissingSchema):
            list(scrape_urls(456))

    def test_url_that_returns_404_error_raises_exception(self):
        self.mock_get.return_value = self.get_resp(raise_for_status=HTTPError)

        with self.assertRaises(HTTPError):
            list(scrape_urls('http://www.google.com/admin'))

    def test_src_url_content_with_correct_class_and_img_urls(self):
        src = 'http://mockkkkkkkk.com'
        src_content = b'''
            <div class="artworks-by-dictionary">http://s.com/fake1.jpg http://s.com/fake2.jpg</div>
        '''

        mock_resp = self.get_resp(content=src_content)
        self.mock_get.return_value = mock_resp

        urls = scrape_urls(src)

        self.assertEqual(sum(1 for _ in urls), 2)

    def test_src_url_content_without_correct_class_and_img_urls(self):
        src = 'http://sitethatdoesnotexist.com'
        src_content = b'<html></html>'

        mock_resp = self.get_resp(content=src_content)
        self.mock_get.return_value = mock_resp

        urls = scrape_urls(src)

        self.assertEqual(sum(1 for _ in urls), 0)


class DownloadImgTest(unittest.TestCase):

    def setUp(self):
        self.patcher_get = mock.patch('wikiwall.requests.get', autospec=True)
        self.mock_get = self.patcher_get.start()

        self.patcher_getcwd = mock.patch(
            'wikiwall.os.getcwd', return_value='/home/gah', autospec=True
        )
        self.mock_getcwd = self.patcher_getcwd.start()

        self.patcher_makedirs = mock.patch(
            'wikiwall.os.makedirs',
            autospec=True,
        )
        self.mock_makedirs = self.patcher_makedirs.start()

        # Suppress print and tqdm output
        self.patcher_print = mock.patch('wikiwall.print')
        self.mock_print = self.patcher_print.start()
        self.patcher_tqdm = mock.patch('wikiwall.tqdm')
        self.mock_tqdm = self.patcher_tqdm.start()

    def tearDown(self):
        self.patcher_get.stop()
        self.patcher_getcwd.stop()
        self.patcher_makedirs.stop()
        self.patcher_print.stop()
        self.patcher_tqdm.stop()

    def test_create_path_without_correct_permissions(self):
        self.mock_makedirs.side_effect = PermissionError

        with self.assertRaises(PermissionError):
            download_img('http://', dest='/usr/bin/jeezusmosesgah')

    def test_invalid_url_with_only_http(self):
        self.mock_get.side_effect = InvalidURL

        with self.assertRaises(InvalidURL):
            download_img('http://')

    def test_invalid_url_without_http(self):
        self.mock_get.side_effect = MissingSchema

        with self.assertRaises(MissingSchema):
            download_img('gahhh.com')

    def test_int_url_raises_error_and_requests_get_not_called(self):
        with self.assertRaises(TypeError):
            download_img(345)

        self.mock_get.assert_not_called()

    def test_int_path_raises_type_error_and_requests_get_not_called(self):
        with self.assertRaises(TypeError):
            download_img('http://www.google.com', path=345)

        self.mock_get.assert_not_called()

    def test_dest_is_not_a_string(self):
        with self.assertRaises(TypeError):
            download_img('http://www.google.com', dest=123)

    @mock.patch('wikiwall.open', new_callable=mock.mock_open)
    def test_requests_get_and_open_called_with_valid_url(self, mock_open):
        download_img('http://www.google.com')

        self.mock_get.assert_called_with('http://www.google.com', stream=True)
        mock_open.assert_called()

    @mock.patch('wikiwall.open', new_callable=mock.mock_open)
    def test_path_with_None_value_becomes_the_cwdir(self, mock_open):
        url = 'http://www.blah.com/jeezus.jpg'

        fullpath = download_img(url=url, dest=None)
        dirpath = os.path.dirname(fullpath)

        self.mock_makedirs.assert_called_with(self.mock_getcwd.return_value)
        self.assertEqual(dirpath, self.mock_getcwd.return_value)

    @mock.patch('wikiwall.open', new_callable=mock.mock_open)
    def test_correct_file_path_returned_based_on_url_passed_in(self, mock_open):
        tempdir = tempfile.TemporaryDirectory()

        url = 'http://www.blah.com/jeezus.jpg'

        expected_fpath = os.path.join(tempdir.name, 'jeezus.jpg')
        filepath = download_img(url=url, dest=tempdir.name)

        self.assertEqual(filepath, expected_fpath)

        tempdir.cleanup()

    @mock.patch('wikiwall.open', new_callable=mock.mock_open)
    def test_write_called_with_valid_url_and_dest(self, mock_open):
        tempdir = tempfile.TemporaryDirectory()

        with mock.patch('wikiwall.tqdm', return_value=['chunk']):
            download_img(url='http://jeezus', dest=tempdir.name)

        mock_open.return_value.write.assert_called()

        tempdir.cleanup()

    def test_file_path_of_downloaded_file_is_an_actual_file(self):
        tempdir = tempfile.TemporaryDirectory()

        url = 'http://www.blah.com/jeezus.jpg'

        filepath = download_img(url=url, dest=tempdir.name)

        self.assertTrue(os.path.isfile(filepath))

        tempdir.cleanup()


class CleanDlsTest(unittest.TestCase):

    def create_dls(self, path, fnum):
        '''Create `fnum` JPEG files in `path`.'''

        for n in range(fnum):
            fname = str(n) + '.jpg'
            with open(os.path.join(path, fname), 'w') as f:
                f.write('faux jpeg file')

    def get_jpegs(self, path):
        '''Return list of JPEG file paths from `path`.

        Note: List is sorted by modification time, oldest to newest
        '''
        jpegs = []
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                if f.lower().endswith('.jpg'):
                    jpegs.append(os.path.join(path, f))

        # sort by modification time, oldest to newest
        jpegs.sort(key=os.path.getmtime)

        return jpegs

    def setUp(self):

        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_negative_limit(self):
        with self.assertRaises(ValueError):
            _clean_dls(limit=-1, path=self.tempdir.name)

    def test_float_limit(self):
        with self.assertRaises(ValueError):
            _clean_dls(limit=4.5, path=self.tempdir.name)

    def test_getcwd_called_when_no_path_given(self):
        with mock.patch(
            'wikiwall.os.getcwd',
            return_value=self.tempdir.name
        ) as mock_getcwd:
            _clean_dls(limit=4, path=None)
        mock_getcwd.assert_called()

    def test_no_removal_when_less_files_than_limit(self):
        limit = 10
        fnum = 5

        self.create_dls(path=self.tempdir.name, fnum=fnum)

        with mock.patch('wikiwall.os.remove', autospec=True) as mock_remove:
            _clean_dls(limit, path=self.tempdir.name)

        self.assertEqual(len(self.get_jpegs(path=self.tempdir.name)), fnum)
        mock_remove.assert_not_called()

    def test_removal_when_more_files_than_limit(self):
        limit = 5
        fnum = 10

        self.create_dls(path=self.tempdir.name, fnum=fnum)

        _clean_dls(limit=limit, path=self.tempdir.name)

        self.assertEqual(len(self.get_jpegs(path=self.tempdir.name)), limit)

    def test_old_files_are_removed_first(self):
        limit = 2
        fnum = 5

        # Before cleanup
        self.create_dls(path=self.tempdir.name, fnum=fnum)

        jpegs = self.get_jpegs(path=self.tempdir.name)

        # Grab oldest 3 files and newest 2.
        old = jpegs[:fnum - limit]
        new = jpegs[-limit:]

        _clean_dls(limit=limit, path=self.tempdir.name)

        # After cleanup
        jpegs = self.get_jpegs(path=self.tempdir.name)

        for j in old:
            self.assertNotIn(j, jpegs)
        for j in new:
            self.assertIn(j, jpegs)


class RunAppScriptTest(unittest.TestCase):

    def setUp(self):
        self.patcher_run = mock.patch(
            'wikiwall.subprocess.run',
            side_effect=wikiwall.subprocess.CalledProcessError(
                returncode=1,
                cmd='gah',
                stderr=b'')
        )
        self.mock_run = self.patcher_run.start()

    def tearDown(self):
        self.patcher_run.stop()

    def test_raise_exception_if_return_code_not_zero(self):

        with self.assertRaises(ValueError):
            _run_appscript('gah')
