import logging
import os
import os.path
import requests
from requests.exceptions import HTTPError, InvalidURL, MissingSchema
import tempfile
import unittest
import unittest.mock as mock
import wikiwall
from wikiwall import (
    _clean_dls,
    _run_appscript,
    download_img,
    get_random,
    scrape_urls,
)


LOGGER = logging.getLogger('wikiwall')


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

        with mock.patch.object(LOGGER, 'warning') as mock_warning:
            get_random(values, k)
        mock_warning.assert_called_with(
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

        return path

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
            _clean_dls(limit=-1)

    def test_float_limit(self):
        with self.assertRaises(ValueError):
            _clean_dls(limit=4.5)

    def test_no_removal_when_less_files_than_limit(self):
        limit = 10
        fnum = 5

        wikiwall.DATA_DIR = self.create_dls(path=self.tempdir.name, fnum=fnum)

        with mock.patch('wikiwall.os.remove', autospec=True) as mock_remove:
            _clean_dls(limit=limit)

        self.assertEqual(len(self.get_jpegs(wikiwall.DATA_DIR)), fnum)
        mock_remove.assert_not_called()

    def test_removal_when_more_files_than_limit(self):
        limit = 5
        fnum = 10

        wikiwall.DATA_DIR = self.create_dls(path=self.tempdir.name, fnum=fnum)

        _clean_dls(limit=limit)

        self.assertEqual(len(self.get_jpegs(wikiwall.DATA_DIR)), limit)

    def test_old_files_are_removed_first(self):
        limit = 2
        fnum = 5

        # Before cleanup
        wikiwall.DATA_DIR = self.create_dls(path=self.tempdir.name, fnum=fnum)

        jpegs = self.get_jpegs(wikiwall.DATA_DIR)

        # Grab oldest 3 files and newest 2.
        old = jpegs[:fnum - limit]
        new = jpegs[-limit:]

        _clean_dls(limit=limit)

        # After cleanup
        jpegs = self.get_jpegs(wikiwall.DATA_DIR)

        for j in old:
            self.assertNotIn(j, jpegs)
        for j in new:
            self.assertIn(j, jpegs)


class RunAppScriptTest(unittest.TestCase):

    def setUp(self):
        self.patcher_popen = mock.patch(
            'wikiwall.subprocess.Popen',
            autospec=True,
        )
        self.mock_popen = self.patcher_popen.start()

    def tearDown(self):
        self.patcher_popen.stop()

    def test_raise_exception_if_return_code_not_zero(self):
        self.mock_popen.return_value.returncode = 1

        with self.assertRaises(ValueError):
            _run_appscript('bad script')


if __name__ == '__main__':
    unittest.main(failfast=True)
