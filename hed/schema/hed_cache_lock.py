"""Support utilities for hed_cache locking"""
import time
import os
import portalocker


TIMESTAMP_FILENAME = "last_update.txt"
CACHE_TIME_THRESHOLD = 300 * 6


class CacheException(Exception):
    """Exception for cache locking or threshold errors."""
    pass


class CacheLock:
    """Class to lock the cache folder to ensure it doesn't get hit by another version at the same time."""
    def __init__(self, cache_folder, write_time=True, time_threshold=CACHE_TIME_THRESHOLD):
        """Constructor for HED locking object

        Parameters:
            cache_folder(str): The folder to create the lock in(implicitly locking that folder)
            write_time(bool): If true, read and write the cache time.  Additionally, won't operate if too recent.
                              Generally False for local operations.
            time_threshold(int): Time before cache is allowed to refresh again.

        """
        self.cache_folder = cache_folder
        self.cache_lock_filename = os.path.join(cache_folder, "cache_lock.lock")
        self.cache_lock = None
        self.timestamp = None
        self.write_time = write_time
        self.time_threshold = time_threshold

    def __enter__(self):
        os.makedirs(self.cache_folder, exist_ok=True)
        last_timestamp = _read_last_cached_time(self.cache_folder)
        self.current_timestamp = time.time()
        time_since_update = self.current_timestamp - last_timestamp
        if time_since_update < self.time_threshold:
            raise CacheException(f"Last updated {time_since_update} seconds ago.  Threshold is {self.time_threshold}")

        try:
            self.cache_lock = portalocker.Lock(self.cache_lock_filename, timeout=1)
        except portalocker.exceptions.LockException:
            raise CacheException(f"Could not lock cache using {self.cache_lock_filename}")
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if self.write_time:
            _write_last_cached_time(self.current_timestamp, self.cache_folder)
        self.cache_lock.release()


def _read_last_cached_time(cache_folder):
    """ Check the given cache folder to see when it was last updated.

    Parameters:
        cache_folder (str): The folder we're caching HED schema in.

    Returns:
        float: The time we last updated the cache.  Zero if no update found.

    """
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)

    try:
        with open(timestamp_filename, "r") as f:
            timestamp = float(f.readline())
            return timestamp
    except FileNotFoundError or ValueError or IOError:
        return 0


def _write_last_cached_time(new_time, cache_folder):
    """ Set the time of last cache update.

    Parameters:
        new_time (float): The time this was updated.
        cache_folder (str): The folder used for caching the HED schema.

    Raises:
        ValueError: Something went wrong writing to the file.
    """
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)
    try:
        with open(timestamp_filename, "w") as f:
            f.write(str(new_time))
    except Exception:
        raise ValueError("Error writing timestamp to hed cache")
