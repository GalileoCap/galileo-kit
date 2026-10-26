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

## Installed

On 2026-10-26, under `~/.local/share/read-aloud/`, for the measurement in `docs/measurements/local-voice-2026-10-26.md`.

- The wheel, `kokoro_onnx-0.6.1-py3-none-any.whl`, SHA-256 `50c8de4950d601df41428ee5462a48c8a78bef441bf671f2492e070ef44d8a32` as PyPI lists it, unpacked into its own folder: its `kokoro_onnx/` is byte for byte `src/kokoro_onnx/` at `659b166` (`diff -r` empty), and its `dist-info` holds no entry point and no `.pth`.
- `kokoro-env`, Python 3.13.13, 122 MB, installed by `uv pip install` from that file: onnxruntime 1.31.1, numpy 2.5.4, phonemizer 3.4.0, espeakng-loader 0.2.4 and nine smaller packages, each resolved to a wheel (`--only-binary :all:` resolves the same set), so no source build ran.
- espeak-ng 1.52.0.1 from nixpkgs, built with `mbrolaSupport = false` (`/nix/store/997zpr4c4fsm2l0h9s96b1niwykdfgvf-espeak-ng-1.52.0.1-unstable-2025-09-09`, 18.6 MB with its closure). The package as nixpkgs ships it pulls in 645 MB of MBROLA voices that Kokoro never uses.
- The weights from `model-files-v1.1`, each matching the digest GitHub publishes for the asset: `kokoro-v1.0.int8.onnx` `ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c`, `kokoro-v1.0.onnx` `beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a`, `voices-v1.0.bin` `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`.
- At run time, with `EspeakConfig` naming nix's library and data, `lsof` shows nix's `libespeak-ng` mapped and espeakng-loader's never. phonemizer copies the library it is given into a fresh temporary folder for each wrapper it builds, four of them in one process, which are copies of nix's build (501,472 bytes, against the loader's 504 KB).
