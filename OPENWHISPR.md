# OpenWhispr Dictation Integration

This branch replaces the active custom KLOR dictation pipeline with [OpenWhispr](https://github.com/OpenWhispr/openwhispr) while keeping the old implementation available for rollback.

## Active path

```text
KLOR firmware
  └─ double-tap RALT → T
       └─ emits F8
            └─ OpenWhispr
                 ├─ records audio
                 ├─ POST /audio/transcriptions
                 │    └─ localhost:8765 adapter
                 │         └─ ElevenLabs Scribe v2
                 ├─ OpenWhispr cleanup / dictionary / snippets
                 └─ inserts text into the focused application
```

The KLOR bridge is not in the audio path. It continues to handle the other command-mode actions.

## Why there is a small adapter

OpenWhispr's Self-Hosted provider expects the OpenAI-style `/audio/transcriptions` multipart contract. ElevenLabs Scribe v2 uses a different endpoint, authentication header and multipart field names. `bridge/openwhispr_elevenlabs_shim.py` only translates those two protocols; it does not record audio, perform custom cleanup, paste text, or own dictation state.

## Existing ElevenLabs API key

No credential is copied into Git.

The adapter resolves the key in this order:

1. `ELEVENLABS_API_KEY`
2. `KLOR_ELEVENLABS_KEY`
3. the existing OS-keyring entry: service `klor-bridge`, username `elevenlabs_key`

`setup.sh` detects that existing keyring entry and reuses it instead of asking for the key again.

## OpenWhispr settings

Configure OpenWhispr once:

- Dictation hotkey: **F8**
- Activation mode: **Toggle**
- Speech to Text provider: **Self-Hosted**
- Server URL: **http://127.0.0.1:8765**
- Model: **scribe_v2**

OpenWhispr sends its custom-dictionary hint as `prompt`; the adapter converts suitable comma/newline-separated terms into ElevenLabs `keyterms[]` fields.

## Services

```bash
systemctl --user enable --now klor-bridge openwhispr-elevenlabs
curl -s http://127.0.0.1:8765/health
journalctl --user -u openwhispr-elevenlabs -f
```

A healthy adapter reports `ok: true`. `elevenlabs_key_configured` should also be true before live transcription.

## Keyboard behavior

- Double-tap RALT: enter command mode.
- T: emit one F8 hotkey tap and immediately exit command mode.
- To toggle dictation off, enter command mode again and press T again.
- Firmware stores no OpenWhispr/dictation-active state.
- RALT, ESC, and other commands keep their normal command-mode behavior; they do not guess whether OpenWhispr is currently recording.

This deliberate statelessness avoids firmware/app state drift if OpenWhispr stops because of an error, cancellation, timeout, or UI action. QMK and ZMK use the same behavior.

## Rollback material

The former custom pipeline is intentionally not deleted on this experiment branch. The old `STTPipeline`, `ACTION_STT (0x10)`, waveform helper, `stt_flow_verify.py`, lexicon/corrections and legacy config remain visible for comparison and rollback. The running bridge sets `LEGACY_STT_ENABLED = False`, and current firmware no longer sends `ACTION_STT`.

Rollback is therefore a code/config switch rather than data recovery. Do not merge/delete the legacy material until the OpenWhispr path has been exercised on the real machine.

## Acceptance test

1. Start OpenWhispr and both user services.
2. Confirm `/health` says the ElevenLabs key is configured.
3. Focus a normal text field.
4. Double-tap RALT, press T, and dictate Danish and English.
5. Double-tap RALT and press T again to stop/toggle OpenWhispr.
6. Confirm OpenWhispr inserts the transcript in the focused field.
7. Repeat after cancelling/stopping once from OpenWhispr's own UI, then verify the next keyboard toggle still behaves correctly (no firmware state drift).
8. Add a distinctive word to OpenWhispr's custom dictionary and confirm it reaches Scribe as a keyterm.
9. Reboot/log in and repeat once to verify autostart/service behavior.
