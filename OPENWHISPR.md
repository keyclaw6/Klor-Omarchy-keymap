# OpenWhispr Dictation Integration

This branch replaces the custom KLOR dictation runtime with [OpenWhispr](https://github.com/OpenWhispr/openwhispr). `main` remains untouched and is the rollback point.

## Active paths

```text
KLOR command mode
├─ T ── Ctrl+Shift+F8 ──> OpenWhispr normal dictation
│               ├─ record / transcribe / cleanup / insert
│               └─ localhost:8765 ──> ElevenLabs Scribe v2
└─ C ── Ctrl+Shift+F9 ──> OpenWhispr Voice Assistant
                └─ native Share screen context ──> screenshot + spoken command
```

The KLOR bridge is in neither voice path. Firmware only emits the dedicated Ctrl+Shift+F8/F9 chords and exits command mode. OpenWhispr owns recording state, screenshot capture, cleanup, assistant routing, and insertion/output.

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

- Dictation hotkey: **Control+Shift+F8**
- Voice Assistant hotkey: **Control+Shift+F9**
- Voice Assistant → **Share screen context: enabled**
- Voice Assistant must use a **vision-capable model** (or configure its dedicated screen-context vision model)
- Dictation activation mode: **Toggle**
- Speech to Text provider: **Self-Hosted**
- Server URL: **http://127.0.0.1:8765**
- Model: **scribe_v2**

OpenWhispr sends its custom-dictionary hint as `prompt`; the adapter converts suitable comma/newline-separated terms into ElevenLabs `keyterms` fields.

## Services

```bash
systemctl --user enable --now klor-bridge openwhispr-elevenlabs
curl -s http://127.0.0.1:8765/health
journalctl --user -u openwhispr-elevenlabs -f
```

A healthy adapter reports `ok: true`. `elevenlabs_key_configured` should also be true before live transcription.

## Keyboard behavior

- Double-tap RALT: enter command mode.
- **T**: emit Ctrl+Shift+F8 once, exit command mode.
- **C**: emit Ctrl+Shift+F9 once, exit command mode.
- Firmware stores no OpenWhispr mode or recording state.
- C does not implement screenshot capture itself; it invokes OpenWhispr's Voice Assistant, whose native screen-context setting owns capture.

This is the entire integration at the keyboard boundary. QMK and ZMK use the same two stateless mappings.

## Rollback

Rollback is Git, not duplicate runtime code: `main` still contains the previous custom dictation implementation. This branch removes that runtime from the bridge and firmware path.

Historical helper/data files such as the old waveform UI, lexicon, and correction YAML may still exist in the repository tree because they are inherited from `main`, but setup does not deploy them and active code does not reference them.

## Acceptance test

1. Start OpenWhispr and both Linux user services.
2. Confirm `/health` says the ElevenLabs key is configured.
3. Set Control+Shift+F8 = Dictation, Control+Shift+F9 = Voice Assistant, and enable Share screen context.
4. In a text field, RALT×2 → T, dictate, then repeat RALT×2 → T to toggle off. Confirm normal transcript insertion.
5. RALT×2 → C and issue a command that depends on visible screen content. Confirm OpenWhispr captures screen context and the assistant uses it.
6. Stop/cancel either mode from OpenWhispr itself, then invoke it again from the keyboard. Confirm there is no firmware state drift.
7. Reboot/log in and repeat once to verify adapter/service startup.
