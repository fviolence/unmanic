#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    unmanic.transfer_tracker.py

    Tracks active file transfers between linked Unmanic installations.
    Provides a thread-safe singleton registry that the RemoteTaskManager
    writes to and the API / WebSocket reads from.

"""
import threading
import time

from unmanic.libs.singleton import SingletonType


class TransferTracker(object, metaclass=SingletonType):
    """
    Thread-safe registry of active transfers between linked installations.

    Each transfer is identified by a unique key (typically the RemoteTaskManager thread name)
    and carries metadata about direction, endpoints, file, status, and transfer type.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._transfers = {}  # key -> dict

    # ------------------------------------------------------------------
    # Writer API  (called from RemoteTaskManager threads)
    # ------------------------------------------------------------------

    def register_transfer(self, transfer_id, data):
        """
        Register or fully replace a transfer entry.

        Expected *data* keys (all optional except file_name):
            file_name           str   basename or relative path of the file
            file_path           str   full path
            direction           str   'send' | 'receive' | 'direct_path'
            from_installation   str   human-readable origin (name or address)
            to_installation     str   human-readable destination
            status              str   'pending' | 'uploading' | 'processing' |
                                      'downloading' | 'complete' | 'failed'
            transfer_type       str   'file_transfer' | 'direct_path_handoff'
            started             float epoch timestamp
            task_id             int   local task id if available
            remote_task_id      int   remote task id if available
            bytes_transferred   int   bytes moved so far (0 for direct_path)
            bytes_total         int   total file size when known
        """
        with self._lock:
            self._transfers[transfer_id] = {
                **data,
                'transfer_id': transfer_id,
                'last_updated': time.time(),
            }

    def update_transfer(self, transfer_id, **fields):
        """Merge *fields* into an existing transfer entry."""
        with self._lock:
            if transfer_id in self._transfers:
                self._transfers[transfer_id].update(fields)
                self._transfers[transfer_id]['last_updated'] = time.time()

    def remove_transfer(self, transfer_id):
        """Remove a transfer entry (task finished or failed)."""
        with self._lock:
            self._transfers.pop(transfer_id, None)

    # ------------------------------------------------------------------
    # Reader API  (called from API handlers / WebSocket)
    # ------------------------------------------------------------------

    def get_all_transfers(self):
        """Return a list of all active transfer dicts (snapshot)."""
        with self._lock:
            return list(self._transfers.values())

    def get_transfer(self, transfer_id):
        """Return a single transfer dict or None."""
        with self._lock:
            entry = self._transfers.get(transfer_id)
            return dict(entry) if entry else None
