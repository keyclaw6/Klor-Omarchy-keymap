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
- T: toggle OpenWhispr dictation immediately.
- T again: stop dictation and exit command mode.
- RALT while dictating: stop dictation without leaking an Alt keystroke.
- ESC while dictating: stop dictation and cancel command mode.
- Another command-mode letter while dictating: stop OpenWhispr first, then dispatch that normal KLOR action.
- The 3-second command timeout is suspended while this command-mode session owns an active OpenWhispr toggle.

QMK and ZMK use the same behavior.

## Rollback material

The former custom pipeline is intentionally not deleted on this experiment branch. The old `STTPipeline`, `ACTION_STT (0x10)`, waveform helper, `stt_flow_verify.py`, lexicon/corrections and legacy config remain visible for comparison and rollback. The running bridge sets `LEGACY_STT_ENABLED = False`, and current firmware no longer sends `ACTION_STT`.

Rollback is therefore a code/config switch rather than data recovery. Do not merge/delete the legacy material until the OpenWhispr path has been exercised on the real machine.

## Acceptance test

1. Start OpenWhispr and both user services.
2. Confirm `/health` says the ElevenLabs key is configured.
3. Focus a normal text field.
4. Double-tap RALT, press T, dictate Danish and English, then press T.
5. Confirm OpenWhispr inserts the transcript in the focused field.
6. Repeat and stop with RALT; confirm no Alt/menu behavior leaks into the app.
7. Repeat and stop with ESC.
8. While dictating, invoke another KLOR command and confirm dictation stops before that command runs.
9. Add a distinctive word to OpenWhispr's custom dictionary and confirm it reaches Scribe as a keyterm.
10. Reboot/log in and repeat once to verify autostart/service behavior.
