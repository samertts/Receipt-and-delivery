"""Tests for build_metadata.py — Build metadata module."""

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestBuildMetadata:
    def test_version_string(self):
        from lab_system.app.build_metadata import VERSION
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    def test_build_date_format(self):
        from lab_system.app.build_metadata import BUILD_DATE
        assert isinstance(BUILD_DATE, str)
        assert "T" in BUILD_DATE or BUILD_DATE == "unknown"

    def test_git_commit(self):
        from lab_system.app.build_metadata import GIT_COMMIT
        assert isinstance(GIT_COMMIT, str)

    def test_git_branch(self):
        from lab_system.app.build_metadata import GIT_BRANCH
        assert isinstance(GIT_BRANCH, str)

    def test_build_number(self):
        from lab_system.app.build_metadata import BUILD_NUMBER
        assert isinstance(BUILD_NUMBER, str)

    def test_python_version(self):
        from lab_system.app.build_metadata import PYTHON_VERSION
        assert isinstance(PYTHON_VERSION, str)
        assert "." in PYTHON_VERSION

    def test_build_type(self):
        from lab_system.app.build_metadata import BUILD_TYPE
        assert isinstance(BUILD_TYPE, str)

    def test_get_build_info(self):
        from lab_system.app.build_metadata import get_build_info
        info = get_build_info()
        assert isinstance(info, dict)
        assert "version" in info
        assert "build_date" in info
        assert "git_commit" in info
        assert "git_branch" in info
        assert "build_number" in info
        assert "python_version" in info
        assert "build_type" in info

    def test_get_version_string(self):
        from lab_system.app.build_metadata import get_version_string
        vs = get_version_string()
        assert isinstance(vs, str)
        assert len(vs) > 0
