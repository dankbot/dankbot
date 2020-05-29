# https://gist.githubusercontent.com/michalc/ab9bd571cfab09216c0316f2302a76b0/raw/f8b187392ccad08d379d2bdfbbbf877132eb8bcf/asyncio_read_write_lock.py

import asyncio
import collections
import contextlib


class Read(asyncio.Future):
    @staticmethod
    def is_compatible(holds):
        return not holds[Write]


class Write(asyncio.Future):
    @staticmethod
    def is_compatible(holds):
        return not holds[Read] and not holds[Write]


class FifoLock:
    def __init__(self):
        self._waiters = collections.deque()
        self._holds = collections.defaultdict(int)

    async def _acquire(self, lock_mode_type):
        lock_mode = lock_mode_type()
        self._waiters.append(lock_mode)
        self._maybe_acquire()

        try:
            await lock_mode
        except asyncio.CancelledError:
            self._maybe_acquire()
            raise

    def _release(self, lock_mode_type):
        self._holds[lock_mode_type] -= 1
        self._maybe_acquire()

    async def acquire_read(self):
        await self._acquire(Read)

    async def acquire_write(self):
        await self._acquire(Write)

    def release_read(self):
        self._release(Read)

    def release_write(self):
        self._release(Write)

    def _maybe_acquire(self):
        while True:
            if not self._waiters:
                break

            if self._waiters[0].cancelled():
                self._waiters.popleft()
                continue

            if self._waiters[0].is_compatible(self._holds):
                waiter = self._waiters.popleft()
                self._holds[type(waiter)] += 1
                waiter.set_result(None)
                continue

            break

    @contextlib.asynccontextmanager
    async def __call__(self, lock_mode_type):
        await self._acquire(lock_mode_type)
        try:
            yield
        finally:
            self._release(lock_mode_type)
