# A local neural voice for read-aloud

The owner finds the system voice too synthetic and asked for a local neural voice, with its memory and CPU cost measured. A delay before the speech starts is acceptable. Written 2026-10-26 at read-aloud 0.1.0, before any candidate was downloaded.

## The machine

An Apple M4 with 16 GB of memory on macOS 27.0.1. `uv` and `ffmpeg` are installed, and `espeak-ng` is absent. Apple's higher voice tiers are not installed: none of the 186 voices `say -v '?'` lists carries a tier in its name, so the system voice heard so far was a basic one.

## What the engine allows

`$.audio.speak` reaches only the system synthesizer. A neural voice runs as a process the plugin starts: `$.process.run` runs a command to its end (30 seconds by default, ten minutes at most), and `$.process.spawn` streams one and kills it when the plugin leaves its loop. So the shape is a synthesis command that writes a WAV per paragraph, and `afplay` spawned to play it. Leaving the `afplay` loop ends the sound at once, as closing the `say` read-aloud 0.2.0 spawns for the system voice does. The next paragraph can be synthesized while the current one plays, so only the first waits.

Two ways to run the model, each to be measured:

- One process per reading. The model loads at each press, and nothing stays in memory between readings.
- A resident server, started by the plugin at the session's start (`$.process.spawn` for the session's life) and asked over `$.http.fetch` on localhost. The model loads once and holds its memory until the session ends.

## The candidates

| Candidate | Runs on | Licence | Code to review | Weights | Notes |
| --- | --- | --- | --- | --- | --- |
| Kokoro-82M through `kokoro-onnx` (thewh1teagle/kokoro-onnx) | CPU, ONNX Runtime | MIT, weights Apache-2.0 | 449 KB repository | 310 MB fp32, 155 MB fp16 or 108 MB int8, plus 26 MB of voices (release `model-files-v1.1`) | The default most comparisons name for English narration on a Mac. Its phonemizer and any bundled espeak-ng are for the review to establish. |
| Piper (OHF-Voice/piper1-gpl, `piper-tts` on PyPI) | CPU | GPL-3.0, each voice its own licence | 25 MB repository | A medium voice is tens of MB (to be read from its model card) | The lightest. Quality is below Kokoro. The original rhasspy/piper was archived in October 2025. It embeds espeak-ng. GPL costs nothing for personal use. |
| Kokoro-82M through `mlx-audio` (Blaizzy/mlx-audio) | GPU, MLX | MIT | 106 MB repository serving about 25 models | Kokoro's MLX weights, size to be read | The same voice on the GPU, so its CPU share may be lower. The code surface is about 230 times kokoro-onnx's, which is the main cost of reviewing it. |

Left out: Chatterbox (0.5B) and Qwen3-TTS (0.6B and up), whose strength is voice cloning, which read-aloud does not need, at several times Kokoro's size. XTTS v2 is slow, its Metal support is reported broken, and its licence forbids commercial use. Cloud voices would send every answer read to a third party (`G5`).

The comparisons this table rests on are SEO-style blogs that contradict each other on details. The licences, sizes and dates come from GitHub's API on 2026-10-26.

## The measurement

Run after each candidate's review, through `session-watched`, on a fixed corpus: ten final answers from the transcripts on disk, turned into utterances by `plugins/read-aloud/hooks/speech.ts`, short (one paragraph), medium and long (about 2,000 characters). The same corpus goes through `say` as the baseline.

For each candidate, in each of the two modes, and at each precision the candidate offers:

- Peak memory: `/usr/bin/time -l`'s maximum resident set size and peak memory footprint, for one reading and, for the server, at rest between readings.
- CPU: user plus system seconds per second of audio, the figure that says what reading costs a session working beside it.
- Delay: seconds from the press to the first sound, cold (the model not loaded) and warm.
- Speed: the real-time factor, seconds of audio per second of synthesis, which must stay above 1 for the next paragraph to be ready before the current one ends.
- Disk: the environment and the weights.
- Quality, judged by the owner: one WAV per candidate and voice of the same two paragraphs, beside `say`.

The figures go to `docs/measurements/local-voice-<date>.md` with the script that produced them, as the other measurements do.

## Order

1. Clone the candidates under `~/devel/galileo/misc/mod-clones/<name>/` at a recorded commit, and write `docs/reviews/<name>.md` for each by the research report's checklist, with its dependency tree from the lock or the package metadata. Nothing from a clone runs.
2. Install each reviewed version from PyPI, pinned, into a `uv` environment of its own outside the clones and this repository, and take the weights from the release or Hugging Face at a pinned revision, with their checksums written into the review.
3. Measure, and hand the owner the WAVs and the figures.
4. Wire the owner's choice into read-aloud: an `engine` option (`system` stays the default), the synthesis command, the `afplay` playback with its immediate stop, and the next paragraph synthesized while the current one plays.

Steps 1 to 3 are done for two candidates. The reviews, `docs/reviews/kokoro-onnx.md` and `docs/reviews/piper-tts.md`, each say install as is under the conditions they list, and each records its install. The figures are in `docs/measurements/local-voice-2026-10-26.md`: Kokoro int8 on 4 threads, one process per reading, costs about 0.29 CPU seconds per second of speech and peaks at 1.1 GB while it synthesizes, and Piper costs a fifth of that CPU and peaks at 480 MB. Step 4 waits on the owner's choice of voice by ear.

I recommend reviewing kokoro-onnx first and Piper as the light baseline, and leaving mlx-audio until kokoro-onnx's CPU cost turns out to be too high, since its review is the largest by far.

## Sources

- [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), [mlx-audio](https://github.com/Blaizzy/mlx-audio), [piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), read 2026-10-26.
- [Best Local TTS for Mac 2026](https://www.promptquorum.com/power-local-llm/best-local-tts-mac), [Best Local TTS Models in 2026](https://www.yaps.ai/blog/best-local-tts-models), [Kokoro vs Piper vs XTTS v2 on M5 Max](https://contracollective.com/blog/kokoro-vs-piper-vs-xtts-local-text-to-speech-m5-max-2026), [Piper TTS review](https://www.promptquorum.com/power-local-llm/piper-tts-review).
