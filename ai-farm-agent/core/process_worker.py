"""Internal worker. Input is released only after the parent attaches its Windows job.

Same-user execution, NOT a security sandbox. Never installs dependencies.
"""
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path


def main():
    payload = json.load(sys.stdin)
    result = {"success": False, "exit_code": 1, "workspace": {}}
    try:
        if payload["mode"] == "command":
            result["exit_code"] = subprocess.call(payload["command"], shell=True)
            result["success"] = result["exit_code"] == 0
        else:
            # Compatibility globals are local to this process; CWD and stdout never affect the UI.
            import base64, collections, csv, datetime, getpass, glob, math, pathlib, random, re, shutil, time
            scope = {name: value for name, value in locals().copy().items() if not name.startswith('_')}
            scope.update({"__name__": "__main__", "workspace": payload.get("workspace", {}),
                          "BASE": str(Path.home()).replace('\\', '/'), "USERNAME": getpass.getuser(),
                          "datetime": datetime.datetime, "os": os, "sys": sys, "json": json,
                          "subprocess": subprocess, "traceback": traceback})
            exec(compile(payload["code"], '<generated>', 'exec'), scope)
            # Only JSON values cross the boundary; live objects are never deserialized.
            for key, value in scope["workspace"].items():
                try:
                    json.dumps(value, allow_nan=False)
                    result["workspace"][key] = value
                except (TypeError, ValueError):
                    continue
            result.update(success=True, exit_code=0)
    except BaseException:
        traceback.print_exc()
    Path(payload["result_path"]).write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
