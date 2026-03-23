import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile


@dataclass
class BaseExecutor:
    box_id: int
    timeout: int
    mem_limit: int

    _sandbox_dir: Path | None = None
    _proc: subprocess.Popen | None = None

    def start_isolation(self) -> None:
        result = subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--init"],
            capture_output=True,
            text=True,
            check=True,
        )
        self._sandbox_dir = Path(result.stdout.strip()) / "box"

    def setup(self, *args, **kwargs) -> None:
        pass

    def start_cmd(self, dirs: list[str], cmd: list[str], *args, **kwargs) -> None:
        assert self._sandbox_dir, "isolation not started"

        options = [f"--box-id={self.box_id}", f"--mem={self.mem_limit}"]
        options += [f"--dir={d}" for d in dirs]

        self._proc = subprocess.Popen(
            args=["isolate"] + options + ["--run", "--"] + cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._sandbox_dir,
            text=True,
        )

    def communicate(self, msg: str | None) -> tuple[str, str] | None:
        assert self._proc is not None

        if self._proc.returncode is not None:
            self.exit()
            raise Exception("Program exited too early.")

        try:
            stdout, stderr = self._proc.communicate(input=msg, timeout=self.timeout)

            if self._proc.returncode in (0, None):
                return stdout, stderr

            self.exit()
            raise Exception(f"Program crashed. {stderr}")
        except subprocess.TimeoutExpired:
            self.exit()
            raise Exception("Time limit exceeded.")

    def exit(self) -> None:
        if self._proc is None:
            return

        self._proc.kill()
        self._proc = None

        subprocess.run(["isolate", f"--box-id={self.box_id}", "--cleanup"], timeout=5)


class CppExecutor(BaseExecutor):
    def setup(self, exec_path: Path) -> None:
        assert self._sandbox_dir

        exec_file = self._sandbox_dir / "exec"
        copyfile(exec_path, exec_file)
        os.chmod(exec_file, 0o755)

    def start_cmd(self) -> None:
        return super().start_cmd(dirs=[], cmd=["./exec"])


class PythonExecutor(BaseExecutor):
    def setup(self, code_path: Path) -> None:
        assert self._sandbox_dir
        copyfile(code_path, self._sandbox_dir / "exec")

    def start_cmd(self) -> None:
        python_path = Path("/opt") / "python-standalone"

        return super().start_cmd(
            dirs=[str(python_path)],
            cmd=[str(python_path / "bin" / "python"), "exec"],
        )


# TODO: fix because g++ is not working
@dataclass
class CompileExecutor:
    box_id: int

    timeout = 30
    mem_limit = 512 * 1024
    out_limit = 10 * 1024

    def run(self, code: str, result_path: Path) -> str | None:
        result = subprocess.run(
            args=["isolate", f"--box-id={self.box_id}", "--init"],
            capture_output=True,
            text=True,
            check=True,
        )
        sandbox_dir = Path(result.stdout.strip()) / "box"

        code_path = sandbox_dir / "code"
        with open(code_path, "w") as f:
            f.write(code)

        options = [
            f"--box-id={self.box_id}",
            f"--mem={self.mem_limit}",
            "--processes=12",
            f"--fsize={self.out_limit}",
            "--dir=/usr",
        ]

        cmd = [
            "/usr/bin/g++",
            code_path.name,
            "-o",
            result_path.name,
            "-static",
            "-O3",
            "-std=c++23",
        ]

        try:
            subprocess.run(
                args=["isolate"] + options + ["--run", "--"] + cmd,
                stderr=subprocess.PIPE,
                cwd=sandbox_dir,
                text=True,
                timeout=self.timeout,
                check=True,
            )
        except subprocess.TimeoutExpired:
            return "Compile time limit reached"
        except subprocess.CalledProcessError as e:
            return e.stderr
        finally:
            subprocess.run(["isolate", f"--box-id={self.box_id}", "--cleanup"])
