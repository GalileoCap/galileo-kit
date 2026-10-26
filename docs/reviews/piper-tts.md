# Review: piper-tts

Piper, a speech engine of the Open Home Foundation that runs VITS voices on ONNX Runtime, the light baseline among read-aloud's candidate voices (`docs/analyses/local-neural-voice.md`). It is a library with a command-line tool, outside what `session-codeintel review` and its validator read. This review reads the clone and the package's PyPI metadata by the research report's checklist turned to a Python package, as `docs/reviews/kokoro-onnx.md` does. Nothing from the clone ran.

| | |
| --- | --- |
| Clone | `~/devel/galileo/misc/mod-clones/piper1-gpl` |
| Origin | `https://github.com/OHF-Voice/piper1-gpl.git` |
| Commit | `74ac24e7e8e2e57a5e1fada5505c74e3d9c1843a`, committed 2026-10-23, 32 commits past `v1.8.0` |
| Release reviewed | 1.8.0 on PyPI (`v1.8.0`, `639388b`), uploaded 2026-09-04. Between the tag and the commit above, the runtime files differ in `voice.py` and `phonemize_espeak.py` only, 40 lines for streaming split voices |
| Licence | GPL-3.0-or-later, each voice under its own model card. Personal use costs nothing |
| Size | 165 files. The runtime is about 2,080 lines across `__init__`, `__main__`, `voice`, `config`, `phonemize_espeak`, `phoneme_ids`, `const`, `download_voices`, `audio_playback`, `http_server` and the C bridge. The macOS arm64 wheel is 33 MB |
| Authors | Michael Hansen, 57 of the last 100 commits, then a dozen contributors. The original `rhasspy/piper` was archived in October 2025 and development moved here |

## What it does

`PiperVoice.load(model_path)` reads a voice's ONNX model and its JSON config, and `synthesize` turns text to sentences, sentences to phonemes through espeak-ng, and phonemes to audio through the model. `python -m piper -m <voice>.onnx -f out.wav` does the same from the command line, reading the text on stdin. `python -m piper.download_voices <name>` fetches a voice from Hugging Face. The `http` extra adds a Flask server, `zh`, `ja` and `th` add other phonemizers, and `train` adds the training code. English speech needs none of the extras.

## Inventory

- `src/piper/`: the package. `espeakbridge.c` (104 lines) is the C extension between Python and espeak-ng.
- `src/piper/train/`: the training code, used only with the `train` extra.
- `src/piper/tashkeel/model.onnx`, `src/piper/hebrew/nakdimon.onnx`: diacritizer models for Arabic and Hebrew, shipped in the wheel, loaded only for those languages.
- `libpiper/`: a C++ library built by its own workflow and left out of the Python wheel.
- `CMakeLists.txt`: fetches espeak-ng from `github.com/espeak-ng/espeak-ng` at commit `724808c` (2026-04-06), builds it static and links it into `espeakbridge`.
- `.github/workflows/`: `test`, `wheels`, `build-libpiper` and `publish`.

## Checklist: malicious behaviour

- Install time. The wheel is prebuilt for `cp39-abi3-macosx_11_0_arm64`, so installing it from PyPI compiles nothing and runs no `setup.py`. A build from the source distribution would run CMake and fetch espeak-ng at the pinned commit. The install takes the wheel.
- Network. Synthesis opens no connection. `download_voices.py` fetches `voices.json` and a voice's two files from `huggingface.co/rhasspy/piper-voices`, only when it is run. The HTTP server downloads a voice it is asked for, and the Chinese phonemizer fetches its g2pW model. read-aloud uses neither.
- Processes. `audio_playback.py` starts `ffplay` to play to the speakers, used only by the command-line tool's play mode. Synthesis to a file starts nothing.
- Files. It reads the voice and its config and writes the WAV it is told to write.
- Loading the files. The voice is ONNX, parsed by ONNX Runtime, with no custom-op library registered. The config is JSON.
- Native code. `espeakbridge`, compiled in CI from the 104-line C file and espeak-ng at a pinned commit, and ONNX Runtime's own library. The C file calls espeak-ng's phonemization API and nothing else: no `system`, `popen`, `dlopen`, socket or environment read.
- Telemetry. None.
- Release. `publish.yml` builds the wheels with cibuildwheel on GitHub's runners and uploads through PyPI Trusted Publishing (`id-token: write`), and PyPI holds a provenance attestation for the macOS arm64 wheel of 1.8.0. The attestation ties the wheel to that workflow at the release's commit.

## Checklist: inefficiency and defects

- Threads. `PiperVoice.load` builds its session with default `SessionOptions`, a thread per core. `PiperVoice(config, session, ...)` can be built by the caller with a capped session, as for Kokoro.
- Memory. A medium English voice is in the tens of MB, read from its model card at download. The wheel carries 33 MB, most of it espeak-ng's data and the two diacritizer models, on disk only.
- Dependencies at run time: onnxruntime and pathvalidate. The smallest tree of the candidates.
- Quality. VITS voices at 22,050 Hz sound flatter than Kokoro's 24,000 Hz output, which the WAVs of the measurement will show the owner.

## Verdict: install as is

Pinned at 1.8.0 from its attested wheel, in a `uv` environment of its own outside the clones, without extras. One English voice, `en_US-lessac-medium` or the owner's pick, from `rhasspy/piper-voices` at a pinned revision, its SHA-256 written here once downloaded. For the measurement, the session is built by read-aloud's script with a capped thread count. No fork.
