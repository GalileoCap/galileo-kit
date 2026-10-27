"""The local-voice measurement: every configuration, the system voice beside them.

    /usr/bin/python3 -I driver.py <base> <corpus.json> <results.json> [<name>,...]

`<base>` holds the environments, the weights and espeak-ng as
`docs/measurements/local-voice-2026-10-26.md` lays them out. Each
configuration runs bench.py under `/usr/bin/time -l` twice over: one process per
reading for three readings (the model loaded at each press), and one process
for all ten (a resident server). The system voice reads every utterance with
`say -o`. The results file holds every figure the report's tables are drawn
from. Names given run those configurations alone, without the system voice,
and a name `say:<voice>` measures `say` in that voice.
"""

import json
import re
import statistics
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLD = ["short-1", "medium-1", "long-1"]
# (name, engine, model file, threads, spinning, arena): threads 0 is ONNX Runtime's own default, a thread per core,
# and the arena is its CPU memory arena, which keeps what it allocated for the next run.
CONFIGS = [
    ("kokoro-int8 as shipped", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", 0, True, True),
    ("kokoro-int8 4 threads", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", 4, False, True),
    ("kokoro-int8 2 threads", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", 2, False, True),
    ("kokoro-fp32 as shipped", "kokoro", "kokoro/kokoro-v1.0.onnx", 0, True, True),
    ("kokoro-fp32 4 threads", "kokoro", "kokoro/kokoro-v1.0.onnx", 4, False, True),
    ("kokoro-fp32 2 threads", "kokoro", "kokoro/kokoro-v1.0.onnx", 2, False, True),
    ("piper as shipped", "piper", "piper/en_US-lessac-medium.onnx", 0, True, True),
    ("piper 2 threads", "piper", "piper/en_US-lessac-medium.onnx", 2, False, True),
    ("piper 1 thread", "piper", "piper/en_US-lessac-medium.onnx", 1, False, True),
    ("kokoro-int8 4 threads no arena", "kokoro", "kokoro/kokoro-v1.0.int8.onnx", 4, False, False),
    ("piper 2 threads no arena", "piper", "piper/en_US-lessac-medium.onnx", 2, False, False),
]


def time_l(stderr: str) -> dict:
    """The figures `/usr/bin/time -l` writes after the command's own stderr."""
    first = re.search(r"([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys", stderr)
    rss = re.search(r"(\d+)\s+maximum resident set size", stderr)
    footprint = re.search(r"(\d+)\s+peak memory footprint", stderr)
    if not (first and rss and footprint):
        raise RuntimeError(f"no time -l figures in: {stderr[-2000:]}")

    return {
        "real_s": float(first.group(1)),
        "cpu_s": float(first.group(2)) + float(first.group(3)),
        "max_rss_mb": int(rss.group(1)) / 2**20,
        "peak_footprint_mb": int(footprint.group(1)) / 2**20,
    }


def run_bench(base: Path, corpus: Path, config: tuple, readings: list, out: Path) -> dict:
    name, engine, model, threads, spinning, arena = config
    spec = {
        "engine": engine,
        "model": str(base / "models" / model),
        "voices": str(base / "models/kokoro/voices-v1.0.bin"),
        "voice": "af_heart",
        "espeak": str(base / "espeak-ng"),
        "threads": threads,
        "spinning": spinning,
        "arena": arena,
        "corpus": str(corpus),
        "readings": readings,
        "out": str(out),
    }
    spec_path = out.with_suffix(".json")
    spec_path.write_text(json.dumps(spec))
    python = base / f"{engine}-env/bin/python"
    start = time.perf_counter()
    child = subprocess.Popen(
        ["/usr/bin/time", "-l", str(python), "-I", str(HERE / "bench.py"), str(spec_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=out.parent,
    )
    events = []
    first_sound_s = None
    assert child.stdout is not None
    for line in child.stdout:
        event = json.loads(line)
        if event["event"] == "utterance" and first_sound_s is None:
            first_sound_s = time.perf_counter() - start
        events.append(event)
    stderr = child.stderr.read() if child.stderr else ""
    if child.wait() != 0:
        raise RuntimeError(f"{name}: bench failed: {stderr[-2000:]}")
    print(f"  {name} {readings or 'all'}: {time.perf_counter() - start:.1f} s", flush=True)

    return {"events": events, "first_sound_s": first_sound_s, **time_l(stderr)}


def stalls(utterances: list) -> float:
    """Seconds of silence between utterances when each is synthesized while the one before plays."""
    ready = 0.0
    playing_until = None
    silence = 0.0
    for one in utterances:
        ready += one["synth_s"]
        if playing_until is None:
            playing_until = ready
        elif ready > playing_until:
            silence += ready - playing_until
            playing_until = ready
        playing_until += one["audio_s"]

    return silence


def summary(cold: list, server: dict) -> dict:
    utterances = [e for e in server["events"] if e["event"] == "utterance"]
    by_reading: dict = {}
    for one in utterances:
        by_reading.setdefault(one["reading"], []).append(one)
    loaded = next(e for e in server["events"] if e["event"] == "loaded")
    done = next(e for e in server["events"] if e["event"] == "done")
    audio = sum(one["audio_s"] for one in utterances)
    synth = sum(one["synth_s"] for one in utterances)
    silences = {reading: stalls(ones) for reading, ones in by_reading.items()}

    return {
        "cold_first_sound_s": [run["first_sound_s"] for run in cold],
        "cold_peak_footprint_mb": max(run["peak_footprint_mb"] for run in cold),
        "cold_max_rss_mb": max(run["max_rss_mb"] for run in cold),
        "cold_cpu_s": [run["cpu_s"] for run in cold],
        "load_wall_s": loaded["wall_s"],
        "load_cpu_s": loaded["cpu_s"],
        "warm_first_sound_s": statistics.median(ones[0]["synth_s"] for ones in by_reading.values()),
        "cpu_per_audio_s": sum(one["cpu_s"] for one in utterances) / audio,
        "cores_busy": sum(one["cpu_s"] for one in utterances) / synth,
        "realtime_factor": audio / synth,
        "slowest_utterance_factor": min(one["audio_s"] / one["synth_s"] for one in utterances),
        "audio_s": audio,
        "silence_s": sum(silences.values()),
        "readings_with_silence": sum(1 for s in silences.values() if s > 0.05),
        "server_rest_rss_mb": done["rss_kb"] / 1024,
        "server_loaded_rss_mb": loaded["rss_kb"] / 1024,
        "server_peak_footprint_mb": server["peak_footprint_mb"],
        "server_max_rss_mb": server["max_rss_mb"],
    }


def wav_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def say_baseline(corpus: Path, out: Path, voice: "str | None" = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    named = [] if voice is None else ["-v", voice]
    rows = []
    for reading in json.loads(corpus.read_text())["readings"]:
        for index, text in enumerate(reading["utterances"]):
            wav = out / f"{reading['id']}-{index:02d}.wav"
            done = subprocess.run(
                ["/usr/bin/time", "-l", "say", *named, "--file-format=WAVE", "--data-format=LEI16@22050", "-o", str(wav), text],
                capture_output=True,
                text=True,
                check=True,
            )
            figures = time_l(done.stderr)
            rows.append({"reading": reading["id"], "index": index, "synth_s": figures["real_s"], "cpu_s": figures["cpu_s"], "audio_s": wav_seconds(wav), "peak_footprint_mb": figures["peak_footprint_mb"], "max_rss_mb": figures["max_rss_mb"]})
    audio = sum(row["audio_s"] for row in rows)

    return {
        "warm_first_sound_s": statistics.median(row["synth_s"] for row in rows if row["index"] == 0),
        "cpu_per_audio_s": sum(row["cpu_s"] for row in rows) / audio,
        "realtime_factor": audio / sum(row["synth_s"] for row in rows),
        "audio_s": audio,
        "peak_footprint_mb": max(row["peak_footprint_mb"] for row in rows),
        "max_rss_mb": max(row["max_rss_mb"] for row in rows),
        "cpu_s_by_reading": {reading: sum(row["cpu_s"] for row in rows if row["reading"] == reading) for reading in COLD},
    }


def main() -> None:
    base, corpus, results_path = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
    only = sys.argv[4].split(",") if len(sys.argv) > 4 else None
    work = Path(tempfile.mkdtemp(prefix="local-voice-"))
    print(f"WAVs under {work}", flush=True)
    results: dict = {"configs": {}}
    if only is None:
        results["say"] = say_baseline(corpus, work / "say")
        print(f"  say: {results['say']}", flush=True)
    for name in [one for one in only or [] if one.startswith("say:")]:
        voice = name[len("say:"):]
        results.setdefault("say_voices", {})[voice] = say_baseline(corpus, work / re.sub(r"\W+", "-", name), voice)
        print(f"  {name}: {results['say_voices'][voice]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    for config in [one for one in CONFIGS if only is None or one[0] in only]:
        slug = re.sub(r"\W+", "-", config[0])
        cold = [run_bench(base, corpus, config, [reading], work / f"{slug}-cold-{reading}") for reading in COLD]
        server = run_bench(base, corpus, config, [], work / f"{slug}-server")
        results["configs"][config[0]] = summary(cold, server)
        results_path.write_text(json.dumps(results, indent=2))
    results_path.write_text(json.dumps(results, indent=2))
    print(f"results in {results_path}", flush=True)


main()
