import shutil
import subprocess
import tempfile

import pytest

from inenv.venv import VirtualEnv, VirtualEnvNotCreatedException


#  These are tests for when a virtualenv has not been created, because it
#  takes too long for unittests.  There is a separate set of tests for when it
#  already exists.
class TestVirtualEnvNotExist(object):
    def setup_method(self):
        self.venv_name = 'test_venv'
        self.venv_dir = tempfile.mkdtemp()
        self.venv = VirtualEnv(self.venv_name, self.venv_dir)

    def teardown_method(self):
        shutil.rmtree(self.venv_dir)

    def test_path(self):
        assert self.venv_name in self.venv.path
        assert self.venv_dir in self.venv.path

    def test_bin_locations(self):
        assert self.venv.path in self.venv.bin_dir
        assert 'bin' in self.venv.bin_dir

    def test_execfile_path(self):
        assert self.venv.path in self.venv.execfile_path
        assert self.venv.execfile_name in self.venv.execfile_path

    def test_cache_file(self):
        assert self.venv.path in self.venv.cache_file
        assert 'cache' in self.venv.cache_file

    def test_save_and_load_cache_file(self):
        # Nothing should be cached yet
        assert self.venv.load_cache_file() == {}
        my_data = {'foo': 'bar', 'some': ['crazy', 1, {'data': "types"}]}

        # Can't cache before creating virtualenv
        with pytest.raises(VirtualEnvNotCreatedException):
            self.venv.save_cache_file(my_data)

    def test_not_exists(self):
        assert not self.venv.exists


#  These are tests for when a virtualenv has already been created
class TestVirtualEnvExists(object):
    def setup_class(self):
        self.venv_name = 'test_venv'
        self.venv_dir = tempfile.mkdtemp()
        self.venv = VirtualEnv(self.venv_name, self.venv_dir)
        self.venv.create()

    def test_save_and_load_cache_file(self):
        # On initialization, the venv hash gets added to the cache
        assert 'venv_hash' in self.venv.load_cache_file()
        my_data = {'foo': 'bar', 'some': ['crazy', 1, {'data': "types"}]}

        self.venv.save_cache_file(my_data)
        assert self.venv.load_cache_file() == my_data

    def test_exists(self):
        assert self.venv.exists

    def test_run(self):
        #  We can verify that the virtual environment changes by inspecting $VIRTUAL_ENV
        #  In this environment, then in our test environment
        echo_virtualenv_cmd = ['echo', '$VIRTUAL_ENV']
        proc = subprocess.Popen(echo_virtualenv_cmd, stdout=subprocess.PIPE)
        proc.wait()
        assert proc.returncode == 0
        venv_dir, _ = proc.communicate()
        assert venv_dir.strip() != self.venv.path

        # Now compare to our test environment
        proc = self.venv.run(echo_virtualenv_cmd, stdout=subprocess.PIPE)
        assert proc.returncode == 0
        test_venv_dir, _ = proc.communicate()
        assert test_venv_dir.strip() == self.venv.path

    def test_run_python(self):
        proc = self.venv.run(['python', '-c', '"print(1 + 1)"'], stdout=subprocess.PIPE)
        assert proc.returncode == 0
        assert proc.communicate() == ('2\n', None)
