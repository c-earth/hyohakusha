"""Preserve optional camera timestamp headers using fake HTTP/JPEG data.

Generated pixels and temporary files are local fixtures. No rover connection
or firmware clock/exposure claim is made by these metadata checks.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

from src.control.timed_camera import TimedCameraRecorder


class CameraMetadataTests(unittest.TestCase):
    """Verify both older responses and timestamp-bearing frames remain usable."""

    def test_optional_header_is_preserved_without_becoming_host_time(self):
        """An absent or arbitrary device timestamp cannot replace host brackets."""
        for timestamp in (None, '123.456789', 'unknown-clock'):
            with self.subTest(timestamp=timestamp), tempfile.TemporaryDirectory() as folder:
                recorder = TimedCameraRecorder('unused.invalid', Path(folder)/'frames')
                ok, encoded = cv2.imencode('.jpg', np.zeros((16, 16, 3), dtype=np.uint8))
                self.assertTrue(ok)
                response = Mock()
                response.read.return_value = encoded.tobytes()
                response.headers = {} if timestamp is None else {'X-Timestamp': timestamp}
                context = Mock()
                context.__enter__ = Mock(return_value=response)
                context.__exit__ = Mock(return_value=False)
                with patch('src.control.timed_camera.urllib.request.urlopen', return_value=context), \
                        patch.object(recorder.stop_event, 'wait', side_effect=lambda seconds: recorder.stop_event.set()), \
                        patch('src.control.connection.socket.create_connection') as dial:
                    recorder.record()
                dial.assert_not_called()
                recorder.worker = Mock()
                recorder.worker.is_alive.return_value = False
                frames = recorder.close()
                self.assertIsNone(recorder.error)
                self.assertEqual(len(frames), 1)
                self.assertEqual(frames[0]['camera_timestamp'], timestamp)
                self.assertGreaterEqual(frames[0]['received_ns'], frames[0]['request_ns'])
                manifest = json.loads((recorder.folder/'frames.json').read_text())
                self.assertEqual(manifest['frames'], frames)


if __name__ == '__main__':
    unittest.main()
