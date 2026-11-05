"""Diagnose local GPT-Live transport. Never sends session.start or microphone audio."""
import json
import os
import sys
from pathlib import Path

APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))


def main():
    from dotenv import load_dotenv
    load_dotenv(APP.parent/'.env');load_dotenv(APP/'.env')
    result={'python':sys.version.split()[0], 'interpreter':sys.executable,
            'session_started':False, 'proxy_configured':any(os.getenv(k) for k in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY'))}
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:
        result['error']='OPENAI_API_KEY ausente'
    else:
        try:
            import websocket
            socket=websocket.create_connection('wss://api.openai.com/v1/live/sessions',
                header={'Authorization':'Bearer '+key},timeout=8,suppress_origin=True,redirect_limit=0)
            result['websocket_status']=socket.getstatus()
            socket.close(timeout=0.1)
        except Exception as error:
            result['error_type']=type(error).__name__
            result['http_status']=getattr(error,'status_code',None)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result.get('websocket_status')==101 else 1


if __name__=='__main__':raise SystemExit(main())
