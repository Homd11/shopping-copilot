"""Ships the host Agent's event records to CloudWatch Logs from its private log file.

The file is the source of truth: records are written there first (deploy.host_event_log)
and this shipper sends new complete lines in batches, remembering how far it got in a
small checkpoint (file identity and offset), so a restart resumes without duplicates
or gaps and an unreachable CloudWatch loses nothing. Debug records are never sent.
"""

import json
import os
import threading
from datetime import datetime
from pathlib import Path

from deploy.host_event_log import DIRECTORY, NAMES

GROUP = "/scpilot/agent-events"
CHECKPOINT = Path("/var/lib/shopping-copilot/agent/log-shipper.json")
INTERVAL_SECONDS = 15
# CloudWatch accepts at most 10,000 events and 1,048,576 bytes (26 bytes overhead each).
BATCH_EVENTS = 1000
BATCH_BYTES = 900_000


class Shipper:
    def __init__(
        self, directory=DIRECTORY, client=None, *, group=GROUP, stream, checkpoint=CHECKPOINT
    ):
        self.directory = Path(directory)
        self.client = client
        self.group = group
        self.stream = stream
        self.checkpoint = Path(checkpoint)
        self.failures = 0
        self._stop = threading.Event()

    def poll(self) -> bool:
        """Send every complete record written since the last checkpoint; True if all went."""
        position = self._load()
        batch, size, done = [], 0, position
        for record, line, after in self._lines(position):
            if record is not None:
                batch.append({"timestamp": record, "message": line})
                size += len(line.encode()) + 26
            if len(batch) >= BATCH_EVENTS or size >= BATCH_BYTES:
                if not self._send(batch):
                    return False
                batch, size = [], 0
                self._save(after)
                done = after
            else:
                done = after
        if batch and not self._send(batch):
            return False
        if done != position:
            self._save(done)
        return True

    def start(self, interval: float = INTERVAL_SECONDS) -> None:
        def loop():
            while not self._stop.wait(interval):
                try:
                    self.poll()
                except Exception:
                    self.failures += 1

        threading.Thread(target=loop, name="event-log-shipper", daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def _lines(self, position):
        """Yield (timestamp or None, line, position after it) oldest first from the checkpoint."""
        files = []
        for name in reversed(NAMES):  # oldest first
            path = self.directory / name
            try:
                files.append((path, path.stat().st_ino))
            except OSError:
                continue
        start = next((i for i, (_, inode) in enumerate(files) if inode == position["inode"]), None)
        for index, (path, inode) in enumerate(files):
            if start is not None and index < start:
                continue
            offset = position["offset"] if index == start else 0
            with open(path, "rb") as file:
                file.seek(offset)
                data = file.read()
            complete = data[: data.rfind(b"\n") + 1]
            for raw in complete.splitlines(keepends=True):
                offset += len(raw)
                text = raw.decode("ascii", "replace").rstrip("\n")
                yield _timestamp(text), text, {"inode": inode, "offset": offset}

    def _send(self, batch) -> bool:
        batch = sorted(batch, key=lambda event: event["timestamp"])
        for attempt in range(2):
            try:
                self.client.put_log_events(
                    logGroupName=self.group, logStreamName=self.stream, logEvents=batch
                )
                return True
            except self.client.exceptions.ResourceNotFoundException:
                if attempt:
                    break
                try:
                    self.client.create_log_stream(
                        logGroupName=self.group, logStreamName=self.stream
                    )
                except self.client.exceptions.ResourceAlreadyExistsException:
                    pass
                except Exception:
                    break
            except Exception:
                break
        self.failures += 1
        return False

    def _load(self):
        try:
            value = json.loads(self.checkpoint.read_text())
            if type(value.get("inode")) is int and type(value.get("offset")) is int:
                return {"inode": value["inode"], "offset": value["offset"]}
        except (OSError, ValueError, AttributeError):
            pass
        return {"inode": None, "offset": 0}

    def _save(self, position) -> None:
        temporary = self.checkpoint.with_name(self.checkpoint.name + ".tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as file:
            json.dump(position, file)
        os.replace(temporary, self.checkpoint)


def _timestamp(text):
    """Milliseconds since the epoch for an ordinary record; None for debug or unreadable lines."""
    try:
        record = json.loads(text)
        if record.get("debug") is True or record.get("event") == "debug":
            return None
        return int(datetime.fromisoformat(record["time"]).timestamp() * 1000)
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
