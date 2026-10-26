# Review: kokoro-onnx

A Python package that runs the Kokoro-82M speech model on ONNX Runtime, a candidate voice for read-aloud (`docs/analyses/local-neural-voice.md`). It is a library, outside what `session-codeintel review` and its validator read. This review reads the clone and the package's PyPI metadata, by the research report's checklist turned to a Python package: what runs at install, what the code reaches, how it loads its files, the binaries it ships, its dependencies and how a release is made. Nothing from the clone ran.

| | |
| --- | --- |
| Clone | `~/devel/galileo/misc/mod-clones/kokoro-onnx` |
| Origin | `https://github.com/thewh1teagle/kokoro-onnx.git` |
| Commit | `3596b26764286a7de9d90c363e988d50578918e5`, committed 2026-09-01 |
| Release reviewed | 0.6.1 on PyPI, uploaded 2026-08-19, bumped in `659b166`. `src/` is identical between `659b166` and the commit above |
| Licence | MIT. The weights are Apache-2.0. Two dependencies, phonemizer and espeak-ng, are GPL-3.0, so the installed whole is GPL-3.0, which costs nothing for personal use |
| Size | 59 files, 1,786 lines of Python in `src/kokoro_onnx/`. The wheel is 25 KB |
| Authors | 207 of 220 commits by `thewh1teagle`, one maintainer |

## What it does

`Kokoro(model_path, voices_path)` loads an ONNX model and a voices file, and `create(text, voice, speed, lang)` returns the samples and the sample rate. Text goes to phonemes through phonemizer's espeak-ng backend (`tokenizer.py`), phonemes to token ids from the vocabulary embedded in the model or shipped as `config.json`, and the ids through the model. Long input is cut into chunks of phonemes (`chunker.py`, `sliding.py`) and the silence at each end trimmed (`trim.py`, vendored from librosa). `create_stream` yields the chunks as they are made. There is no command-line tool: the examples are scripts a caller writes.

## Inventory

- `src/kokoro_onnx/`: the package, nine modules.
- `examples/`: 27 scripts, none installed by the wheel.
- `scripts/export.py`, `scripts/fetch_voices.py`: the maintainer's tools to export the model from hexgrad/Kokoro-82M and to fetch the voices, run by the `fetch_voices` workflow and left out of the wheel.
- `.github/workflows/`: `check`, `test`, `fetch_voices` and `publish-to-pypi`.
- `uv.lock`: 24 packages, development ones included.

## Checklist: malicious behaviour

- Install time. The build backend is hatchling, with no build hook and no `setup.py`, and the wheel is pure Python. Installing it runs nothing of the package's.
- Network. No module of the package opens a connection. The URLs in the source are in error messages telling the user where to download the files, and in comments.
- Processes. None started. No `subprocess`, `os.system`, `eval` or `exec`.
- Files. It reads the model, the voices file, an optional vocabulary JSON and its own `config.json`. It writes nothing.
- Environment. `LOG_LEVEL` (logging to stderr), `ONNX_PROVIDER` (the execution provider) and `PHONEMIZER_ESPEAK_LIBRARY` (the espeak-ng library's path).
- Loading the files. The voices file goes through `np.load` with pickling left off, numpy's default since 1.16.3, so an object array in it is refused. The model is ONNX, a protobuf graph that ONNX Runtime parses. The package registers no custom-op library, so a model cannot load native code through it. A malformed model is a parser's problem, the reason to take the weights at a pinned release with their checksums.
- Native code. `tokenizer.py` loads espeak-ng with `ctypes.cdll.LoadLibrary` from the path `espeakng-loader` gives, or `PHONEMIZER_ESPEAK_LIBRARY`, or the system's. `espeakng-loader` 0.2.4 is the same maintainer's package, a 9.6 MB macOS arm64 wheel holding a prebuilt `libespeak-ng` and its data, built by a manually started workflow of `thewh1teagle/espeakng-loader` and uploaded 2025-01-17. Of this candidate's binaries, it alone is built by a single person. `EspeakConfig(lib_path, data_path)` replaces it, so nix's espeak-ng, built from source, can be loaded in its place, and `espeakng-loader`'s library is then installed and never loaded.
- Telemetry. None. The log is Python's `logging` on stderr, at WARNING by default.
- Release. `publish-to-pypi.yml` is started by hand and uploads with an API token (`PYPI_TOKEN`), without Trusted Publishing, so PyPI holds no provenance attestation for 0.6.1. The wheel is to be compared with `src/` at `659b166` before it runs.

## Checklist: inefficiency and defects

- Threads. `create_session` builds an `InferenceSession` with the default options, so ONNX Runtime takes a thread per core and a reading would compete with the session's own work. `Kokoro.from_session(session, voices_path)` takes a session the caller builds, so `intra_op_num_threads` can be capped. The measurement takes both.
- Memory. The model is 310 MB at full precision, 155 MB at fp16 and 108 MB at int8 (release `model-files-v1.1`), with 26 MB of voices. All of it is resident while a process holds the model.
- Phonemization holds a process-wide lock (`_espeak_lock`), since espeak-ng keeps global state. One reading at a time is what read-aloud does anyway.
- Dependencies at run time: onnxruntime (with flatbuffers, protobuf, sympy, mpmath and packaging), numpy, phonemizer (with joblib, attrs, dlinfo and typing-extensions) and espeakng-loader. About thirteen packages, every one widely used except espeakng-loader.

## Verdict: install as is

Pinned at 0.6.1 in a `uv` environment of its own outside the clones, with:

1. The wheel compared file by file with `src/kokoro_onnx/` at `659b166` before anything imports it.
2. espeak-ng taken from nix and passed through `EspeakConfig`, so `espeakng-loader`'s binary never loads.
3. The weights from the `model-files-v1.1` release, their SHA-256 written here once downloaded: `kokoro-v1.0.int8.onnx` (108 MB), `kokoro-v1.0.onnx` (310 MB) and `voices-v1.0.bin` (26 MB).
4. The session built by read-aloud's own script with a capped thread count, through `Kokoro.from_session`.

No fork: read-aloud needs none of its code changed, and its upstream is small enough to diff at each update.
