"""The owner's listening samples: the same two paragraphs in every voice measured.

    /usr/bin/python3 -I samples.py <base> <corpus.json> <out folder> [<say voice>...]

The paragraphs are the first two utterances of the corpus's `medium-1`. Each
voice's WAV is the two read one after the other with half a second between.
System voices named after the folder are read by `say` alone, and the neural
voices are then left out.
"""

import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
# (file name, engine, model file, Kokoro voice)
VOICES = [
    ("kokoro-int8-af_heart", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", "af_heart"),
    ("kokoro-fp32-af_heart", "kokoro", "kokoro/kokoro-v1.0.onnx", "af_heart"),
    ("kokoro-int8-af_bella", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", "af_bella"),
    ("kokoro-int8-am_michael", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", "am_michael"),
    ("kokoro-int8-bf_emma", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", "bf_emma"),
    ("kokoro-int8-bm_george", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", "bm_george"),
    ("piper-lessac-medium", "piper", "piper/en_US-lessac-medium.onnx", ""),
]


def join(parts: list, out: Path) -> None:
    with wave.open(str(parts[0]), "rb") as first:
        params = first.getparams()
    gap = b"\x00" * (params.sampwidth * params.nchannels * params.framerate // 2)
    with wave.open(str(out), "wb") as joined:
        joined.setparams(params)
        for index, part in enumerate(parts):
            with wave.open(str(part), "rb") as one:
                joined.writeframes(one.readframes(one.getnframes()))
            if index < len(parts) - 1:
                joined.writeframes(gap)


def main() -> None:
    base, corpus, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    medium = next(one for one in json.loads(corpus.read_text())["readings"] if one["id"] == "medium-1")
    paragraphs = medium["utterances"][:2]
    work = Path(tempfile.mkdtemp(prefix="local-voice-samples-"))
    sample_corpus = work / "corpus.json"
    sample_corpus.write_text(json.dumps({"readings": [{"id": "sample", "utterances": paragraphs}]}))

    say_voices = sys.argv[4:]
    for name, engine, model, voice in [] if say_voices else VOICES:
        spec = {
            "engine": engine,
            "model": str(base / "models" / model),
            "voices": str(base / "models/kokoro/voices-v1.0.bin"),
            "voice": voice,
            "espeak": str(base / "espeak-ng"),
            "threads": 4,
            "spinning": False,
            "corpus": str(sample_corpus),
            "out": str(work / name),
        }
        spec_path = work / f"{name}.json"
        spec_path.write_text(json.dumps(spec))
        subprocess.run([str(base / f"{engine}-env/bin/python"), "-I", str(HERE / "bench.py"), str(spec_path)], check=True, capture_output=True, cwd=work)
        join(sorted((work / name).glob("sample-*.wav")), out / f"{name}.wav")
        print(out / f"{name}.wav", flush=True)

    for voice in say_voices or [""]:
        named = ["-v", voice] if voice else []
        parts = []
        for index, text in enumerate(paragraphs):
            part = work / f"say-{index}.wav"
            subprocess.run(["say", *named, "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(part), text], check=True)
            parts.append(part)
        slug = re.sub(r"\W+", "-", voice).strip("-").lower() or "default"
        target = out / f"say-{slug}.wav"
        join(parts, target)
        print(target, flush=True)


main()
