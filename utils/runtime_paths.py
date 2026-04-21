import os
import sys
from functools import lru_cache


@lru_cache(maxsize=1)
def source_root():
	return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_root():
	meipass_path = getattr(sys, "_MEIPASS", None)
	if getattr(sys, "frozen", False) and meipass_path:
		return meipass_path
	return source_root()


def writable_root():
	if getattr(sys, "frozen", False):
		return os.path.dirname(sys.executable)
	return source_root()


def resource_path(*parts):
	return os.path.join(resource_root(), *parts)


def writable_path(*parts):
	return os.path.join(writable_root(), *parts)