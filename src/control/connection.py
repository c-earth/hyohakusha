"""Own one sequential rover TCP connection without experiment or file policy.

RoverConnection supplies tagged requests, fault handling, heartbeats and stop
cleanup. Subclasses implement event recording and their own movement limits.
Command state tracks host dispatch, not physical motion or observed rest.
"""

import json
import select
import socket
import threading
import time

from .protocol import FirmwareFault


class RoverConnection:
    """Keep all TCP operations on one thread and serialize rover actions.

    address is the rover IP/hostname; construction opens no connection. sock,
    buffer and timestamp brackets belong to this owner. Only N2/N3 may observe
    a drive, with one pending sensor request. A drive remains reserved until
    N100 is sent; a pan remains reserved until its reply. Neither proves rest.
    HTTP observers receive no reference to this connection.
    """

    SENSOR_COMMANDS = (1, 2, 3, 7, 8)

    def __init__(self, address):
        """Initialize disconnected transport state for the supplied address."""
        self.address = address
        self.sock = None
        self.buffer = ''
        self.sequence = 0
        self.heartbeat_at = 0.0
        self.last_send_bracket = None
        self.last_receive_ns = None
        self._owner_thread = threading.get_ident()
        self._action = None
        self._pending_sensor = None

    def _check_owner(self):
        """Reject transport access from a thread other than the creator."""
        if threading.get_ident() != self._owner_thread:
            raise RuntimeError('Rover TCP belongs to one controller thread')

    def connect(self):
        """Open TCP port 100 once, with a 2 s connect and 50 ms I/O timeout."""
        self._check_owner()
        if self.sock is not None:
            raise RuntimeError('Controller already owns a connection')
        self.sock = socket.create_connection((self.address, 100), timeout=2)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.settimeout(0.05)

    def event(self, kind, **payload):
        """Receive event name/fields; subclasses supply evidence persistence."""
        pass

    def _reserve(self, number, tag):
        """Reserve dispatch state or reject overlapping actions before I/O.

        number is an allowed firmware command ID and tag its unique string.
        N100 is always permitted by the action gate, including pending reads.
        A failed transmission retains reservations until stop/close cleanup.
        """
        if number == 100:
            return
        if self._action is not None:
            if self._action[0] != 4 or number not in (2, 3):
                raise RuntimeError('Movement/pan must finish before another action')
        if number in self.SENSOR_COMMANDS:
            if self._pending_sensor is not None:
                raise RuntimeError('Only one sensor request may be pending')
            self._pending_sensor = (number, tag)
        elif number in (4, 5, 6):
            if self._pending_sensor is not None:
                if number != 4 or self._pending_sensor[0] not in (2, 3):
                    raise RuntimeError('Pending sensor must finish before this action')
            self._action = (number, tag)

    def send(self, command):
        """Send an allowed command dict or heartbeat; return its tag or None.

        Subclasses constrain PWM/duration. Brackets cover socket send only,
        excluding later event writes. Stop is transmitted before releasing the
        action reservation, even when the event logger subsequently fails.
        """
        self._check_owner()
        tag = None
        if isinstance(command, dict):
            command = dict(command)
            if command['N'] not in (1, 2, 3, 4, 5, 6, 7, 8, 100):
                raise ValueError('Unsupported command')
            self.sequence += 1
            tag = f'c{self.sequence}'
            command['H'] = tag
            message = json.dumps(command, separators=(',', ':'))
            self._reserve(command['N'], tag)
        else:
            if command != '{Heartbeat}':
                raise ValueError('Invalid raw message')
            message = command
        begin_ns = time.monotonic_ns()
        self.sock.sendall(message.encode('ascii'))
        self.last_send_bracket = dict(begin_ns=begin_ns, complete_ns=time.monotonic_ns())
        if isinstance(command, dict) and command['N'] == 100:
            self._action = None
        if message == '{Heartbeat}':
            self.heartbeat_at = time.monotonic()
        self.event('send', message=message, **self.last_send_bracket)
        return tag

    def _receive_state(self, frame):
        """Release matching sensor/pan reservations after a complete reply.

        Old installed firmware can retag N4 completion to the pending IMU tag;
        its 'ok' is not the requested vector and must not release that read.
        """
        if self._pending_sensor is not None:
            number, tag = self._pending_sensor
            prefix = '{' + tag + '_'
            if frame.startswith(prefix):
                if number not in (2, 3) or frame[len(prefix):-1] != 'ok':
                    self._pending_sensor = None
        if self._action is not None and self._action[0] in (5, 6):
            if frame.startswith('{' + self._action[1] + '_'):
                self._action = None

    def poll(self):
        """Return ready brace frames; log and raise every firmware fault.

        Faults for unrelated tags also end acquisition. Receipt timestamps are
        shared by frames in one recv batch and exclude later log-write time.
        """
        self._check_owner()
        replies = []
        if select.select([self.sock], [], [], 0)[0]:
            data = self.sock.recv(4096)
            self.last_receive_ns = time.monotonic_ns()
            if not data:
                raise ConnectionError('Peer closed')
            self.buffer += data.decode('ascii', errors='strict')
            if len(self.buffer) > 8192:
                raise ValueError('Receive buffer overflow')
            while '}' in self.buffer:
                end = self.buffer.index('}') + 1
                frame, self.buffer = self.buffer[:end], self.buffer[end:]
                start = frame.find('{')
                if start >= 0:
                    frame = frame[start:]
                    self.event('receive', message=frame, received_ns=self.last_receive_ns)
                    FirmwareFault.check_frame(frame)
                    self._receive_state(frame)
                    replies.append(frame)
        return replies

    def wait(self, seconds):
        """Maintain heartbeat and receive logging for nonnegative seconds."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if time.monotonic() - self.heartbeat_at >= 0.4:
                self.send('{Heartbeat}')
            self.poll()
            time.sleep(0.002)

    def request(self, command):
        """Send a command and return its matching reply within 2 s.

        Heartbeats continue while waiting. N100 accepts its legacy untagged
        acknowledgment; an IMU-tagged drive acknowledgment is ignored.
        """
        tag = self.send(command)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            for frame in self.poll():
                if command['N'] == 100 and frame == '{ok}':
                    return 'ok'
                prefix = '{' + tag + '_'
                if frame.startswith(prefix):
                    content = frame[len(prefix):-1]
                    if command['N'] not in (2, 3) or content != 'ok':
                        return content
            if time.monotonic() - self.heartbeat_at >= 0.4:
                self.send('{Heartbeat}')
            time.sleep(0.002)
        raise TimeoutError(f'No reply for {tag}')

    def close(self):
        """Attempt N100/receipt logging and close even if stop/logging fails.

        Cleanup records distinguish a closed socket from observed physical
        rest. A failed event write cannot prevent release of the connection.
        """
        self._check_owner()
        if self.sock is None:
            return
        stop_error = None
        try:
            self.send(dict(N=100))
            self.wait(0.2)
        except BaseException as error:
            stop_error = str(error) or type(error).__name__
            try:
                self.event('cleanup_failure', error=str(error))
            except Exception:
                pass
            print(f'Cleanup warning: {error}', flush=True)
        finally:
            self.sock.close()
            self.sock = None
            self._action = self._pending_sensor = None
            try:
                self.event('cleanup', stop_attempted=True, socket_closed=True,
                           stop_error=stop_error, physical_rest_verified=False)
            except Exception as error:
                print(f'Cleanup logging warning: {error}', flush=True)
