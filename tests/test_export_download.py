"""Exercise real exporter results, including multi-file ZIPs, through the result page."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from local_beta import views
from tests.test_xsd_validation import XSDValidationBase


class ExportDownloadTests(XSDValidationBase):
    def test_real_single_and_zip_results_offer_automatic_and_manual_download(self):
        _, uid1 = self._seed('MDR')
        _, uid2 = self._seed('MDR')
        for limit, ids in ((300, [uid1]), (1, [uid1, uid2])):
            with self.subTest(limit=limit):
                with patch('local_beta.exporter.BULK_UPLOAD_ENTITY_LIMIT', limit):
                    result = self.exporter.export('DEVICE.POST', ids)
                self.assertFalse(result['errors'])
                result['action'] = 'export'
                html = views.export_page('DEVICE.POST', self.repo.get_udis_by_ids(ids), result)
                self.assertIn('window.location.assign(link.href)', html)
                self.assertIn('/download/' + Path(result['file_path']).name, html)
                self.assertLess(html.index('id="result"'), html.index('id="export-form"'))
                self.assertEqual(Path(result['file_path']).suffix, '.zip' if limit == 1 else '.xml')
                for item in result['files']:
                    self.assertTrue(Path(item['file_path']).is_file())

    def test_precheck_and_errors_do_not_start_download(self):
        _, uid = self._seed('MDR')
        result = self.exporter.validate('DEVICE.POST', [uid])
        result['action'] = 'preflight'
        html = views.export_page('DEVICE.POST', [], result)
        self.assertNotIn('window.location.assign(link.href)', html)
        result.update(action='export', errors=['blocked'])
        self.assertNotIn('window.location.assign(link.href)', views.export_page('DEVICE.POST', [], result))

    def test_same_second_exports_keep_distinct_history_files(self):
        _, uid = self._seed('MDR')
        with patch('local_beta.exporter.datetime') as clock:
            clock.now.return_value = datetime(2026, 9, 15, 12, 0, 0)
            first = self.exporter.export('DEVICE.POST', [uid])
            original = Path(first['file_path']).read_bytes()
            second = self.exporter.export('DEVICE.POST', [uid])
        self.assertNotEqual(first['file_path'], second['file_path'])
        self.assertEqual(Path(first['file_path']).read_bytes(), original)


class ExportNavigationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js required for browser-script regression')
    def test_saved_filters_restore_only_when_no_result_is_present(self):
        html = views.export_page('DEVICE.POST', [])
        function = re.search(r'  function restoreExportPageIfNeeded\(\).*?(?=  function syncExportUrl)', html, re.S).group()
        script = """
const assert = require('node:assert/strict');
const vm = require('node:vm');
for (const hasResult of [true, false]) {
  const redirects = [];
  const context = {
    URLSearchParams,
    document: {getElementById: () => hasResult ? {} : null},
    window: {location: {pathname: '/export', search: '', replace: url => redirects.push(url)}},
    loadExportQuery: () => 'service_type=DEVICE.POST&record_ids=1',
    saveExportQuery: () => {}
  };
  vm.createContext(context);
  vm.runInContext(FUNCTION, context);
  assert.equal(vm.runInContext('restoreExportPageIfNeeded()', context), !hasResult);
  assert.deepEqual(redirects, hasResult ? [] : ['/export?service_type=DEVICE.POST&record_ids=1']);
}
""".replace('FUNCTION', json.dumps(function))
        subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
