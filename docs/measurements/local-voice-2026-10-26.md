# What a local neural voice costs read-aloud

Measured on 2026-10-26 by the plan in `docs/analyses/local-neural-voice.md`, for the two candidates reviewed in `docs/reviews/kokoro-onnx.md` and `docs/reviews/piper-tts.md`, with the system voice beside them. The owner asked for the memory and CPU cost, and said a delay before the speech is acceptable.

## How it was measured

- The machine: an Apple M4 (4 performance and 6 efficiency cores) with 16 GB, macOS 27.0.1. Python 3.13.13, onnxruntime 1.31.1 on the CPU, kokoro-onnx 0.6.1, piper-tts 1.8.0, espeak-ng 1.52.0.1 from nix for Kokoro.
- The corpus: ten final answers from this project's transcripts, three short (136 to 230 characters), four medium (602 to 1,327) and three long (2,116 to 2,296), 10,588 characters in all, turned into utterances by `plugins/read-aloud/hooks/speech.ts` as the plugin reads them. That is 11 to 12 minutes of speech. `local-voice/corpus.mjs` picks them, and keeps the corpus itself outside this repository.
- `local-voice/driver.py` runs each configuration twice over, under `/usr/bin/time -l`, through `local-voice/bench.py` in the candidate's own environment. **One process per reading**: three processes, for one short, one medium and one long answer, each loading the model at the press. **A resident server**: one process loads the model once and reads all ten. Each utterance becomes one WAV, as the plugin would write it. The system voice reads every utterance with `say -o`.
- A configuration is the model, the number of ONNX Runtime's threads, whether its idle threads spin, and whether its CPU memory arena is on. *As shipped* is what each package does by itself: a thread per core, spinning, arena on. The capped configurations turn spinning off.
- The raw figures are in `local-voice/results-2026-10-26.json` and `local-voice/results-arena-2026-10-26.json`.

What the figures can and cannot say: each configuration ran once. While the Kokoro configurations ran, this session ran the plugin's tests, a type-check and two short headless sessions, one of them a `say`, which may have raised those figures a little. The arena-off runs and the samples ran on an otherwise idle session. `say`'s CPU counts the `say` process alone: during a probe, no speech daemon gained CPU time. The cold delay includes Python's start and its imports.

## Delay and speed

The first sound is the seconds from the press to the first paragraph's WAV, the moment `afplay` could start. Cold is one process per reading, over the three readings. Warm is the server's median over the ten. Speed is seconds of speech per second of synthesis over the corpus, and the slowest utterance is the lowest of those ratios for one paragraph. In every configuration, each paragraph was ready before the one before it finished playing, so no reading had a silence between paragraphs, and the first wait is the only one.

| Configuration | First sound, cold | First sound, warm | Speed | Slowest utterance |
| --- | --- | --- | --- | --- |
| Kokoro int8, as shipped | 2.6 to 4.1 s | 1.34 s | 8.3× | 5.1× |
| Kokoro int8, 4 threads | 2.5 to 3.6 s | 1.27 s | 9.9× | 6.3× |
| Kokoro int8, 2 threads | 2.9 to 4.2 s | 1.60 s | 7.8× | 5.4× |
| Kokoro int8, 4 threads, no arena | 2.6 to 3.6 s | 1.35 s | 8.0× | 3.7× |
| Kokoro fp32, as shipped | 3.7 to 5.9 s | 2.62 s | 4.6× | 3.0× |
| Kokoro fp32, 4 threads | 3.8 to 6.3 s | 2.76 s | 4.3× | 2.9× |
| Kokoro fp32, 2 threads | 5.3 to 9.6 s | 4.77 s | 2.8× | 1.7× |
| Piper, as shipped | 1.0 to 1.2 s | 0.26 s | 41× | 28× |
| Piper, 2 threads | 1.1 to 1.4 s | 0.37 s | 29× | 24× |
| Piper, 1 thread | 1.3 to 2.0 s | 0.58 s | 18× | 16× |
| Piper, 2 threads, no arena | 1.2 to 1.6 s | 0.43 s | 27× | 21× |
| `say` | | 0.72 s | 15× | |

## Memory

In MB. Loaded is the resident set once the model is ready. The peak is `time -l`'s peak memory footprint, for one process per reading (the highest of the three) and for the server. At rest is the server's resident set two seconds after its last reading.

| Configuration | Loaded | Peak, per reading | Peak, server | Server at rest |
| --- | --- | --- | --- | --- |
| Kokoro int8, as shipped | 258 | 1,090 | 1,272 | 1,118 |
| Kokoro int8, 4 threads | 258 | 1,083 | 1,267 | 1,255 |
| Kokoro int8, 2 threads | 258 | 1,082 | 1,266 | 1,184 |
| Kokoro int8, 4 threads, no arena | 257 | 1,402 | 2,008 | 658 |
| Kokoro fp32, as shipped | 473 | 1,177 | 1,414 | 1,240 |
| Kokoro fp32, 4 threads | 473 | 1,172 | 1,410 | 1,003 |
| Kokoro fp32, 2 threads | 482 | 1,177 | 1,375 | 866 |
| Piper, as shipped | 139 | 484 | 493 | 527 |
| Piper, 2 threads | 139 | 475 | 478 | 488 |
| Piper, 1 thread | 139 | 483 | 482 | 458 |
| Piper, 2 threads, no arena | 143 | 843 | 849 | 456 |
| `say`, per utterance | | 11 | | |

## CPU

CPU seconds (user and system) per second of speech, over the corpus in the server. Cores busy is CPU time over synthesis time, how many cores a reading takes while it synthesizes. The last column is the CPU of a whole process per reading, start and load included, for the short (209 characters), medium (602) and long (2,116) answer.

| Configuration | CPU per second of speech | Cores busy | Short, medium, long answer |
| --- | --- | --- | --- |
| Kokoro int8, as shipped | 0.57 s | 4.7 | 7.8, 20.7, 83.1 s |
| Kokoro int8, 4 threads | 0.29 s | 2.8 | 4.3, 11.1, 44.8 s |
| Kokoro int8, 2 threads | 0.22 s | 1.7 | 3.5, 8.9, 34.4 s |
| Kokoro int8, 4 threads, no arena | 0.33 s | 2.7 | 4.4, 11.4, 44.1 s |
| Kokoro fp32, as shipped | 1.04 s | 4.8 | 12.9, 37.6, 151.7 s |
| Kokoro fp32, 4 threads | 0.79 s | 3.4 | 9.6, 27.9, 124.5 s |
| Kokoro fp32, 2 threads | 0.67 s | 1.9 | 8.3, 23.7, 100.7 s |
| Piper, as shipped | 0.12 s | 5.0 | 2.0, 4.4, 17.0 s |
| Piper, 2 threads | 0.06 s | 1.9 | 1.4, 2.6, 9.7 s |
| Piper, 1 thread | 0.06 s | 1.0 | 1.3, 2.4, 8.2 s |
| Piper, 2 threads, no arena | 0.07 s | 1.9 | 1.8, 3.3, 10.7 s |
| `say` | 0.013 s | | |

## Disk

Kokoro: its environment 125 MB, the int8 model 109 MB, the voices 27 MB, and espeak-ng 19 MB from nix (the fp32 model another 310 MB). Piper: its environment 147 MB and the voice 60 MB. Everything is under `~/.local/share/read-aloud/`.

## What the figures say

- Spinning threads cost half the CPU, for nothing. As shipped, ONNX Runtime takes a thread per core and lets idle ones spin. Capped at 4 threads with spinning off, Kokoro int8 costs 0.29 CPU seconds per second of speech against 0.57, and is faster too. Piper halves the same way. Whatever engine read-aloud uses, it builds its own session.
- Kokoro needs about 1.1 GB while it synthesizes, whatever its precision or threads. Loaded, int8 holds 258 MB, and the first synthesis takes the process past 1 GB. A server would keep 1.1 to 1.25 GB resident between readings. With the arena off, the resident set at rest halves, but the peak rises to 1.4 GB per reading and 2.0 GB in the server, so the arena stays on.
- One process per reading is the shape. The model loads in half a second, so the cold first sound is only 1.2 to 2.3 s later than the warm one, and the memory is released when the reading's synthesis ends. At 10× real time, a medium answer's synthesis is over in about 4 seconds while its 40 seconds of speech play from WAVs, so the 1.1 GB is held for the synthesis alone.
- fp32 costs 2.7 times int8's CPU at 4 threads. It is less than half as fast, and its first sound comes about 1.5 seconds later. Whether it sounds better is for the owner's ear.
- Piper costs a fifth of Kokoro's CPU: 0.06 CPU seconds per second of speech, a first sound one second after the press, and a peak of 480 MB. The reviews expected its voice to sound flatter.
- Every configuration keeps ahead of playback, Kokoro fp32 on 2 threads included, so synthesizing the next paragraph while one plays leaves no silence.

For Kokoro int8, 4 threads, spinning off and arena on, with one process per reading: a medium answer of 600 characters costs about 11 CPU seconds and 1.1 GB for about 4 seconds, and its first sound comes 2.5 to 3.6 seconds after the press. A long answer of 2,100 characters costs about 45 CPU seconds over 15 seconds. That is the configuration I recommend, if the owner prefers Kokoro's voice by ear. Piper, 2 threads, is the choice if the voice is close enough and the cost should be the lowest.

## The samples

The same two paragraphs (the first two of the medium answer `medium-1`) in each voice, made by `local-voice/samples.py` into `~/.local/share/read-aloud/samples/`: Kokoro int8 with `af_heart`, `af_bella`, `am_michael`, `bf_emma` and `bm_george`, Kokoro fp32 with `af_heart`, Piper's `en_US-lessac-medium`, and `say`'s default voice.

## Not measured

- A paragraph's length against Kokoro's peak memory and first sound: cutting long paragraphs at sentence ends may lower both.
- CPU taken from the session working beside a reading: the cores-busy column is the reading's share, measured with no other load.
- Kokoro fp16 (155 MB) and Piper's other voices and qualities.
