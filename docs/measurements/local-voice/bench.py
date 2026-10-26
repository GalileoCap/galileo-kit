"""One process of the local-voice measurement, run by a candidate's own Python.

    <env>/bin/python -I bench.py <spec.json>

The spec names the engine, the model, the voice, the ONNX threads, the readings
and the folder for the WAVs. The process loads the model once and reads each
reading utterance by utterance, writing one WAV per utterance as read-aloud
would. It prints one JSON line per event on stdout: `loaded`, then one
`utterance` per utterance (the first flushed as soon as its WAV is written, so
the driver can time the first sound), one `reading` per reading with the
resident memory after it, and `done`.
"""

import json
import os
import resource
import subprocess
import sys
import time
import wave
from pathlib import Path


def emit(event: str, **fields: object) -> None:
    print(json.dumps({"event": event, **fields}), flush=True)


def cpu_seconds() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_utime + usage.ru_stime


def resident_kb() -> int:
    out = subprocess.run(["/bin/ps", "-o", "rss=", "-p", str(os.getpid())], capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


def session(model: str, threads: int, spinning: bool, arena: bool):
    import onnxruntime as ort

    options = ort.SessionOptions()
    options.enable_cpu_mem_arena = arena
    if threads > 0:
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
    if not spinning:
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
        options.add_session_config_entry("session.inter_op.allow_spinning", "0")

    return ort.InferenceSession(model, sess_options=options, providers=["CPUExecutionProvider"])


def write_wav(path: Path, samples, rate: int) -> float:
    import numpy as np

    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())

    return len(pcm) / rate


def kokoro_engine(spec: dict):
    from kokoro_onnx import EspeakConfig, Kokoro

    espeak = spec["espeak"]
    tts = Kokoro.from_session(
        session(spec["model"], spec["threads"], spec["spinning"], spec.get("arena", True)),
        spec["voices"],
        espeak_config=EspeakConfig(lib_path=f"{espeak}/lib/libespeak-ng.dylib", data_path=f"{espeak}/share/espeak-ng-data"),
    )

    def speak(text: str, path: Path) -> float:
        samples, rate = tts.create(text, voice=spec["voice"], speed=1.0, lang="en-us")
        return write_wav(path, samples, rate)

    return speak


def piper_engine(spec: dict):
    from piper import PiperVoice
    from piper.config import PiperConfig

    with open(f"{spec['model']}.json", encoding="utf-8") as config:
        voice = PiperVoice(config=PiperConfig.from_dict(json.load(config)), session=session(spec["model"], spec["threads"], spec["spinning"], spec.get("arena", True)))

    def speak(text: str, path: Path) -> float:
        with wave.open(str(path), "wb") as out:
            voice.synthesize_wav(text, out)
        with wave.open(str(path), "rb") as done:
            return done.getnframes() / done.getframerate()

    return speak


def main() -> None:
    spec = json.loads(Path(sys.argv[1]).read_text())
    out = Path(spec["out"])
    out.mkdir(parents=True, exist_ok=True)
    readings = json.loads(Path(spec["corpus"]).read_text())["readings"]
    wanted = spec.get("readings")
    if wanted:
        readings = [one for one in readings if one["id"] in wanted]

    start, cpu = time.perf_counter(), cpu_seconds()
    speak = {"kokoro": kokoro_engine, "piper": piper_engine}[spec["engine"]](spec)
    emit("loaded", wall_s=time.perf_counter() - start, cpu_s=cpu_seconds() - cpu, rss_kb=resident_kb())

    for reading in readings:
        for index, text in enumerate(reading["utterances"]):
            start, cpu = time.perf_counter(), cpu_seconds()
            audio = speak(text, out / f"{reading['id']}-{index:02d}.wav")
            emit("utterance", reading=reading["id"], index=index, chars=len(text), synth_s=time.perf_counter() - start, cpu_s=cpu_seconds() - cpu, audio_s=audio)
        emit("reading", reading=reading["id"], rss_kb=resident_kb())

    time.sleep(2)
    emit("done", rss_kb=resident_kb())


main()
