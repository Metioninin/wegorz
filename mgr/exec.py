import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile

from pexpect.popen_spawn import PopenSpawn
import pexpect


class ExecutionError(Exception):
    pass


@dataclass
class BaseExecutor:
    box_id: int

    timeout: float
    mem_limit: int
    exit_timeout: int = 5

    _sandbox_dir: Path | None = None
    _proc: PopenSpawn | None = None
    _setup_finished: bool = False

    _stdout_length: int = 0
    _stderr_length: int = 0

    def start_isolation(self) -> None:
        subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--cleanup"],
            timeout=self.exit_timeout,
            check=True,
        )
        result = subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--init"],
            capture_output=True,
            text=True,
            check=True,
        )
        self._sandbox_dir = Path(result.stdout.strip()) / "box"

    def setup_sandbox(self, *args, **kwargs) -> None:
        self._setup_finished = True

    def run(self, dirs: list[str], cmd: list[str], *args, **kwargs) -> None:
        assert self._sandbox_dir, "isolation not started"
        assert self._setup_finished, "setup not finished"

        options = [f"--box-id={self.box_id}", f"--mem={self.mem_limit}", "-s"]
        options += [f"--dir={d}" for d in dirs]

        self._proc = PopenSpawn(
            cmd=["isolate"] + options + ["--run", "--"] + cmd,
            cwd=self._sandbox_dir,
            encoding="utf-8",
        )

    def send_line(self, line: str):
        assert self._proc
        self._proc.sendline(line)

    def read_string(self) -> str:
        assert self._proc

        result = self._proc.expect(
            pattern=[r"\S+\s+", pexpect.TIMEOUT, pexpect.EOF],
            timeout=self.timeout,
        )

        match result:
            case 0:
                assert isinstance(self._proc.after, str)
                return self._proc.after
            case 1:
                raise ExecutionError("Time limit exceeded")
            case 2:
                raise ExecutionError("Expected output, but reached EOF")
            case _:
                raise NotImplementedError()

    def exit(self) -> None:
        if self._proc is None:
            return

        self._proc.kill(signal.SIGKILL)
        self._proc = None

        subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--cleanup"],
            timeout=self.exit_timeout,
        )


class CppExecutor(BaseExecutor):
    def setup_sandbox(self, exec_path: Path) -> None:
        assert self._sandbox_dir

        exec_file = self._sandbox_dir / "exec"
        copyfile(exec_path, exec_file)
        os.chmod(exec_file, 0o755)

        super().setup_sandbox()

    def run(self) -> None:
        return super().run(dirs=[], cmd=["./exec"])


class PythonExecutor(BaseExecutor):
    def setup_sandbox(self, code_path: Path) -> None:
        assert self._sandbox_dir
        copyfile(code_path, self._sandbox_dir / "exec")
        super().setup_sandbox()

    def run(self) -> None:
        python_path = Path("/opt") / "python-standalone"
        return super().run(
            dirs=[str(python_path)],
            cmd=[str(python_path / "bin" / "python"), "exec"],
        )


COMPILE_TIMEOUT = 30
COMPILE_ISO_TIMEOUT = 5
COMPILE_MEM_LIMIT = 512 * 1024
COMPILE_OUT_LIMIT = 10 * 1024


def compile_cpp(code: str, result_path: Path, box_id: int) -> None:
    subprocess.run(
        args=["isolate", f"--box-id={box_id}", "--cleanup"],
        timeout=COMPILE_ISO_TIMEOUT,
        check=True,
    )
    result = subprocess.run(
        args=["isolate", f"--box-id={box_id}", "--init"],
        capture_output=True,
        text=True,
        check=True,
    )
    sandbox_dir = Path(result.stdout.strip()) / "box"

    code_path = sandbox_dir / "code.cpp"
    with open(code_path, "w") as f:
        f.write(code)

    options = [
        f"--box-id={box_id}",
        f"--mem={COMPILE_MEM_LIMIT}", # NOTE: vulnerability, works only for one process
        "--processes=1024", # no limit
        f"--fsize={COMPILE_OUT_LIMIT}",
        "--dir=/usr",
    ]
    cmd = [
        "/usr/bin/g++",
        "-o",
        "./out",
        "./code.cpp",
        "-static",
        "-O3",
        "-std=c++20",
        "-B/usr/bin/",
    ]

    try:
        subprocess.run(
            args=["isolate"] + options + ["--run", "--"] + cmd,
            stderr=subprocess.PIPE,
            cwd=sandbox_dir,
            text=True,
            timeout=COMPILE_TIMEOUT,
            check=True,
        )
    except subprocess.TimeoutExpired:
        raise ExecutionError("Compile time limit reached")
    except subprocess.CalledProcessError as e:
        raise ExecutionError(f"Compilation failed\n{e.stderr}")
    else:
        copyfile(sandbox_dir / "out", str(result_path))
    finally:
        subprocess.run(["isolate", f"--box-id={box_id}", "--cleanup"])
