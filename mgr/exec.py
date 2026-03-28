import os
import select
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile
from threading import Thread
from typing import IO

from mgr.helpers import EXC_OUT_LIMIT


class ExecutionError(Exception):
    pass


@dataclass
class BaseExecutor:
    box_id: int

    timeout: float
    mem_limit: int
    exit_timeout: int = 5

    _sandbox_dir: Path | None = None
    _proc: subprocess.Popen | None = None
    _setup_finished: bool = False
    _running: bool = False

    def start_isolation(self) -> None:
        assert self._sandbox_dir is None
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
        assert self._setup_finished, "setup not finished"
        assert not self._running, "already running"

        options = [f"--box-id={self.box_id}", f"--mem={self.mem_limit}", "-s"]
        options += [f"--dir={d}" for d in dirs]

        self._proc = subprocess.Popen(
            args=["isolate"] + options + ["--run", "--"] + cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._sandbox_dir,
            bufsize=0,
            text=True,
        )
        self._running = True

    def send_line(self, line: str):
        assert self._proc
        assert self._proc.stdin
        assert self._running, "not running"

        try:
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()
        except BrokenPipeError:
            pass

    def read_string(self) -> str:
        assert self._proc
        assert self._proc.stdout
        assert self._running, "not running"

        l_word: list[str] = []
        l_exception: list[Exception] = []

        def _read_string(stdout: IO, l_exception: list, l_word: list) -> None:
            try:
                # wait for stdout
                _, _, _ = select.select([stdout], [], [])

                word = ""
                word_started: bool = False

                while True:
                    char = os.read(stdout.fileno(), 1)

                    if char == b"":
                        break

                    if char.isspace():
                        if word_started:
                            break
                        else:
                            continue

                    word += char.decode()
                    word_started = True

                    if len(word) > EXC_OUT_LIMIT:
                        raise ExecutionError(
                            f"Output is too long, max is {EXC_OUT_LIMIT} chars per query"
                        )

                l_word.append(word)
            except Exception as e:
                l_exception.append(e)

        t = Thread(
            target=_read_string,
            args=(self._proc.stdout, l_exception, l_word),
            daemon=True,
        )
        t.start()
        t.join(timeout=self.timeout)

        if l_exception:
            raise l_exception[0]

        if t.is_alive():
            self._proc.poll()
            match self._proc.returncode:
                case None:
                    raise ExecutionError("Time limit exceeded for anwser")
                case 0:
                    raise ExecutionError("Expected output, but got EOF")
                case _:
                    if self._proc.stderr:
                        stderr = self._proc.stderr.read(EXC_OUT_LIMIT)
                    else:
                        stderr = ""
                    raise ExecutionError(f"Runtime error\n{stderr}")

        assert len(l_word) == 1
        
        if l_word[0] == "":
            raise ExecutionError("Expected output, but got EOF")
        return l_word[0]

    def exit(self) -> None:
        if self._proc is None:
            return

        self._sandbox_dir = None
        self._setup_finished = False
        self._running = False

        self._proc.kill()
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
        f"--mem={COMPILE_MEM_LIMIT}",  # NOTE: vulnerability, works only for one process
        "--processes=1024",  # no limit
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
