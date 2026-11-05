"""Opt-in paid Live test with synthetic text; never records the microphone."""
import argparse
import json
import sys
import threading
import wave
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-live', action='store_true', help='explicitly permit one paid Live session')
    args = parser.parse_args()
    if not args.allow_live:
        parser.error('Use --allow-live somente se autorizar uma sessao cobrada pelo provedor.')
    from dotenv import load_dotenv
    load_dotenv(APP.parent / '.env'); load_dotenv(APP / '.env')
    from core.config import get_config
    from core.voice.live import LiveNarrator, RATE, MODEL
    narrator = LiveNarrator(get_config().get('voice.live', {}))
    out = APP / 'memory' / 'live-voice-smoke'
    out.mkdir(parents=True, exist_ok=True)
    try:
        clip = narrator.render('Olá. A integração de voz está pronta para o teste.', threading.Event())
        if clip is None:
            raise ValueError('Audio ausente')
        with wave.open(str(out / 'voice.wav'), 'wb') as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(RATE)
            stream.writeframes(clip.tobytes())
        result = {'model': MODEL, 'passed': True, 'seconds_audio': round(len(clip) / RATE, 2),
                  'usage': narrator.last_usage, 'human_listening_validated': False}
    except Exception as error:
        result = {'model': MODEL, 'passed': False, 'error_type': type(error).__name__,
                  'usage': narrator.last_usage, 'human_listening_validated': False}
    (out / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))  # metadata only: no provider body, key, transcript or audio
    return 0 if result['passed'] else 1


if __name__ == '__main__': raise SystemExit(main())
