import unittest
from unittest.mock import patch
from local_beta.constants import GITEE_RELEASES_API_URL
from local_beta.update_checker import check_latest_release, release_download_links


class GiteeUpdateTests(unittest.TestCase):
    def test_config_uses_latest_endpoint(self):
        self.assertTrue(GITEE_RELEASES_API_URL.endswith('/releases/latest'))

    def test_oldest_first_list_selects_highest_version_for_both_entrypoints(self):
        releases = [{'tag_name': tag, 'assets': []} for tag in ['v0.7.2', 'v1.0.2', 'v0.9.9', 'v1.0.1']]
        with patch('local_beta.update_checker._fetch_json', return_value=(releases, '', '')):
            result = check_latest_release('', '1.0.1', mirror_api_url=GITEE_RELEASES_API_URL)
            self.assertEqual(result['latest_version'], '1.0.2')
            self.assertEqual(result['status'], 'ok')
            result = release_download_links('', GITEE_RELEASES_API_URL)
            self.assertEqual(result['gitee']['version'], '1.0.2')
            self.assertTrue(result['gitee']['page_url'].endswith('/v1.0.2'))

    def test_latest_not_found_falls_back_to_larger_list(self):
        with patch('local_beta.update_checker._fetch_json', side_effect=[
            (None, 'not_found', '404'),
            ([{'tag_name': 'v0.7.2'}, {'tag_name': 'v1.0.1'}], '', '')
        ]) as fetch:
            result = check_latest_release('', '1.0.1', mirror_api_url=GITEE_RELEASES_API_URL)
            self.assertEqual(result['status'], 'up_to_date')
            self.assertTrue(fetch.call_args.args[0].endswith('/releases?per_page=100'))
