"""Bounded same-user worker processes. This is process containment, not a sandbox.

Windows Job Objects kill descendants on close. If job setup fails, no user code is released.
https://learn.microsoft.com/windows/win32/procthread/job-objects
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import threading
from contextlib import contextmanager
from pathlib import Path

OUTPUT_LIMIT = 1024 * 1024
WORKSPACE_LIMIT = 256 * 1024


@contextmanager
def _working_directory():
    directory = tempfile.TemporaryDirectory(prefix='ai-farm-worker-')
    try:
        yield directory.name
    finally:
        # Windows can release inherited file handles just after process exit is signalled.
        for attempt in range(40):
            try:
                directory.cleanup()
                break
            except PermissionError:
                if attempt == 39:
                    raise
                time.sleep(0.05)


def _attach_job(process):
    if os.name != 'nt':
        return None
    import win32job
    job = win32job.CreateJobObject(None, '')
    try:
        limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
        limits['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        limits['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS | win32job.JOB_OBJECT_LIMIT_JOB_MEMORY
        limits['BasicLimitInformation']['ActiveProcessLimit'] = 8
        limits['JobMemoryLimit'] = 1024 * 1024 * 1024
        win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
        win32job.AssignProcessToJobObject(job, int(process._handle))
        return job
    except Exception:
        job.Close()
        raise


class _Output:
    """Drain an inherited pipe continuously while retaining at most the configured limit."""
    def __init__(self, stream):
        self.stream, self.data = stream, bytearray()
        self.overflow = threading.Event()
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        try:
            while True:
                block = self.stream.read(16384)
                if not block:
                    break
                available = OUTPUT_LIMIT - len(self.data)
                self.data.extend(block[:max(0, available)])
                if len(block) > available:
                    self.overflow.set()
        except (OSError, ValueError):
            pass

    def finish(self):
        self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise RuntimeError('Pipe de processo descendente permaneceu aberto.')
        self.stream.close()
        return self.data.decode('utf-8', 'replace')


def _run(payload, *, cwd=None, timeout=60, should_stop=None):
    stop = should_stop or (lambda: False)
    result = {'success': False, 'status': 'failed', 'verified': False, 'exit_code': None, 'result': ''}
    if stop():
        return {**result, 'status': 'cancelled', 'result': 'Cancelado antes de iniciar.'}
    timeout = max(0.05, min(float(timeout), 120))
    worker = Path(__file__).with_name('process_worker.py')
    with _working_directory() as tmp:
        root = Path(tmp)
        payload['result_path'] = str(root / 'result.json')
        encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if len(encoded) > WORKSPACE_LIMIT * 4:
            return {**result, 'result': 'Entrada do worker excede o limite.'}
        process, job, stdout, stderr = None, None, None, None
        output, errors = '', ''
        try:
            environment = {k: v for k, v in os.environ.items() if k.upper() in {
                'SYSTEMROOT', 'WINDIR', 'PATH', 'USERPROFILE', 'HOMEDRIVE', 'HOMEPATH', 'APPDATA',
                'LOCALAPPDATA', 'TMP', 'TEMP', 'COMSPEC', 'PROGRAMFILES', 'PROGRAMFILES(X86)',
                'PROGRAMDATA', 'USERNAME', 'LANG', 'LC_ALL'}}
            environment['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen([sys.executable, '-u', str(worker)], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd or tmp,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                start_new_session=os.name != 'nt', env=environment)
            stdout, stderr = _Output(process.stdout), _Output(process.stderr)
            job = _attach_job(process)
            process.stdin.write(encoded)
            process.stdin.close()
            deadline = time.monotonic() + timeout
            while process.poll() is None:
                if stop():
                    result.update(status='cancelled', result='Execucao cancelada.')
                    break
                if time.monotonic() >= deadline:
                    result.update(status='timeout', result='Tempo limite de execucao atingido.')
                    break
                if stdout.overflow.is_set() or stderr.overflow.is_set():
                    result.update(status='output_limit', result='Limite de saida excedido.')
                    break
                manifest = root / 'result.json'
                if manifest.exists() and manifest.stat().st_size > OUTPUT_LIMIT:
                    result.update(status='output_limit', result='Manifesto excede limite de saida.')
                    break
                time.sleep(0.025)
            else:
                result['exit_code'] = process.returncode
                manifest = root / 'result.json'
                if manifest.exists() and manifest.stat().st_size <= OUTPUT_LIMIT:
                    data = json.loads(manifest.read_text(encoding='utf-8'))
                    result.update(success=data.get('success') is True and process.returncode == 0,
                                  exit_code=data.get('exit_code', process.returncode))
                    workspace = data.get('workspace', {})
                    if isinstance(workspace, dict) and len(json.dumps(workspace)) <= WORKSPACE_LIMIT:
                        result['workspace'] = workspace
                result['status'] = 'succeeded' if result['success'] else 'failed'
        except Exception as error:
            result.update(success=False, status='failed', result=f'Worker indisponivel: {error}')
        finally:
            if job is not None:
                import win32job
                try:
                    win32job.TerminateJobObject(job, 1)
                    until = time.monotonic() + 10
                    while win32job.QueryInformationJobObject(job, win32job.JobObjectBasicAccountingInformation)['ActiveProcesses']:
                        if time.monotonic() >= until:
                            raise RuntimeError('A arvore nao confirmou encerramento.')
                        time.sleep(0.025)
                finally:
                    job.Close()
            elif process is not None and os.name != 'nt':
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
            if stdout is not None:
                output = stdout.finish()
            if stderr is not None:
                errors = stderr.finish()
        if stdout is not None and (stdout.overflow.is_set() or stderr.overflow.is_set()):
            result.update(success=False, status='output_limit', result='Limite de saida excedido.')
        if result['status'] in ('succeeded', 'failed') and not result['result']:
            result['result'] = (output + ('\n' + errors if errors else '')).strip()[:8000] or (
                'Processo concluido.' if result['success'] else 'Processo falhou.')
        return result


def run_python(code, workspace=None, **kwargs):
    return _run({'mode': 'python', 'code': code, 'workspace': workspace or {}}, **kwargs)


def run_command(command, **kwargs):
    return _run({'mode': 'command', 'command': command}, **kwargs)
