"""Control-flow tests for actual QR detection with decoder candidates mocked."""
import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch

import numpy as np


VALID = '000000000001||NGUOI DEMO|01011990|Nam|DIA CHI DEMO|01012021'


class QRDetectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # No native library is required for these candidate-selection tests.
        zbar_stub = types.ModuleType('pyzbar')
        zbar_stub.pyzbar = None
        with patch.dict(sys.modules, {'cv2': types.ModuleType('cv2'), 'pyzbar': zbar_stub}):
            # test_docx_fields may already have imported this module with stubs.
            cls.module = importlib.import_module('src.services.cccd_scanner')

    def setUp(self):
        self.scanner = object.__new__(self.module.CCCDScanner)
        self.scanner.parser = self.module.QRCodeParser()
        self.scanner.qr_detector = Mock()
        self.scanner.qr_detector.detectAndDecodeMulti.return_value = (False, (), None, None)
        self.image = np.zeros((10, 10), np.uint8)
        self.zbar = types.SimpleNamespace(decode=Mock(return_value=[]),
                                         ZBarSymbol=types.SimpleNamespace(QRCODE=64))

    def detect(self):
        with patch.object(self.module, 'pyzbar', self.zbar):
            return self.scanner._detect_qr(self.image)

    def test_only_qr_symbols_and_valid_candidates(self):
        self.zbar.decode.return_value = [
            types.SimpleNamespace(type='CODE128', data=VALID.encode()),
            types.SimpleNamespace(type='QRCODE', data=b'https://example.invalid'),
            types.SimpleNamespace(type='QRCODE', data=b'\xff'),
            types.SimpleNamespace(type='QRCODE', data=VALID.encode()),
        ]
        self.assertEqual(self.detect(), VALID)
        self.assertEqual(self.zbar.decode.call_args.kwargs['symbols'], [64])

    def test_opencv_tries_all_decoded_qrs(self):
        self.scanner.qr_detector.detectAndDecodeMulti.return_value = (
            True, ('https://example.invalid', VALID), None, None,
        )
        self.assertEqual(self.detect(), VALID)

    def test_unrelated_qr_is_not_identity_data(self):
        self.zbar.decode.return_value = [types.SimpleNamespace(type='QRCODE', data=b'plain text')]
        self.scanner.qr_detector.detectAndDecodeMulti.return_value = (True, ('plain text',), None, None)
        self.assertIsNone(self.detect())

    def test_dates_and_empty_name_must_pass_parser_validation(self):
        self.scanner.qr_detector.detectAndDecodeMulti.return_value = (
            True, (VALID.replace('01011990', '31021990'), VALID.replace('NGUOI DEMO', '')), None, None,
        )
        self.assertIsNone(self.detect())

    def test_reserved_empty_columns_are_accepted_by_detection(self):
        extended = VALID + '||||'
        self.zbar.decode.return_value = [types.SimpleNamespace(type='QRCODE', data=extended.encode())]
        self.assertEqual(self.detect(), extended)

    def test_right_angle_rotation_keeps_all_portrait_pixels(self):
        portrait = np.arange(24, dtype=np.uint8).reshape(6, 4)
        for angle in (90, 180, 270):
            rotated = self.scanner._rotate_image(portrait, angle)
            self.assertEqual(sorted(rotated.ravel()), sorted(portrait.ravel()))
            self.assertEqual(rotated.shape, (6, 4) if angle == 180 else (4, 6))

    def test_processing_time_uses_monotonic_clock(self):
        result = self.module.CCCDScanResponse(success=False, message='synthetic')
        with patch.object(self.scanner, '_decode_base64_image', return_value=self.image), \
                patch.object(self.scanner, '_multi_stage_detection', return_value=result), \
                patch.object(self.module.time, 'perf_counter', side_effect=[100.0, 100.25]), \
                patch.object(self.module.time, 'time', side_effect=AssertionError('wall clock must not be used')):
            self.assertEqual(self.scanner.scan('synthetic').processing_time, 0.25)


if __name__ == '__main__':
    unittest.main()
