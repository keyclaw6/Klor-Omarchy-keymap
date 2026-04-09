# 03 — Validation Audit

<think>
Phase 4 reasoning: Cross-reference the extraction map (01) against the scaling strategy (02)
to verify every key, encoder, action, and snippet has coordinate space allocated in the
ASCII art plan. This is the quality gate before generating the final ASCII file.

Checklist approach:
1. Verify all 42 keys × 5 layers are extracted
2. Verify encoders × 5 layers are extracted
3. Verify command mode actions are all listed
4. Verify all 22 snippets are cataloged
5. Verify the coordinate system can accommodate every element
6. Flag any conflicts or missing items
</think>

## Audit 1: Key Count Verification

### Per-Layer Key Slots

| Layer     | Expected Keys | Extracted Keys | XXXXXXX (none) | _______ (trans) | Status |
|-----------|---------------|----------------|----------------|-----------------|--------|
| 0 QWERTY  | 42            | 42             | 0              | 0               | PASS   |
| 1 LOWER   | 42            | 42             | 0              | 14              | PASS   |
| 2 RAISE   | 42            | 42             | 0              | 10              | PASS   |
| 3 ADJUST  | 42            | 42             | 10             | 8               | PASS   |
| 4 NAV     | 42            | 42             | 22             | 2               | PASS   |

**Total: 210 key slots extracted (42 × 5 layers). All accounted for.**

### Physical Position Verification

| Position | Row 0 (5+5) | Row 1 (6+6) | Row 2 (6+6+2enc) | Thumb (4+4) | Total |
|----------|-------------|-------------|-------------------|-------------|-------|
| Left     | 5           | 6           | 6 + 1 enc         | 4           | 21+1  |
| Right    | 5           | 6           | 6 + 1 enc         | 4           | 21+1  |
| **Total**| 10          | 12          | 12 + 2 enc        | 8           | **42+2** |

**PASS: 42 keys + 2 encoder positions match LAYOUT_polydactyl macro.**

---

## Audit 2: Encoder Map Verification

| Layer   | Left CCW/CW         | Right CCW/CW          | Extracted? |
|---------|----------------------|------------------------|------------|
| QWERTY  | VolDn/VolUp          | BrightDn/BrightUp      | YES        |
| LOWER   | VolDn/VolUp          | BrightDn/BrightUp      | YES        |
| RAISE   | VolDn/VolUp          | BrightDn/BrightUp      | YES        |
| ADJUST  | VolDn/VolUp          | BrightDn/BrightUp      | YES        |
| NAV     | PrevWS/NextWS        | PrevWS/NextWS          | YES        |

**PASS: 5 layers × 2 encoders × 2 directions = 20 encoder actions, all extracted.**

---

## Audit 3: Command Mode Actions

### Active Actions (9)

| Key | Action          | In extraction map? | In firmware? | In actions.yml? |
|-----|-----------------|---------------------|-------------|-----------------|
| E   | prompt_expand   | YES                 | 0x45        | YES             |
| G   | fix_grammar     | YES                 | 0x47        | YES             |
| I   | improve_writing | YES                 | 0x49        | YES             |
| R   | write_email     | YES                 | 0x52        | YES             |
| S   | summarize       | YES                 | 0x53        | YES             |
| D   | translate_da_en | YES                 | 0x44        | YES             |
| N   | translate_en_da | YES                 | 0x4E        | YES             |
| T   | stt_toggle      | YES                 | 0xFF→0x10   | YES             |
| P   | prompt_picker   | YES                 | 0x50        | YES             |

**PASS: All 9 active actions verified across extraction, firmware, and bridge config.**

### Unconfigured Placeholders (17)

A, B, C, F, H, J, K, L, M, O, Q, U, V, W, X, Y, Z

Count check: 26 letters - 9 active (D,E,G,I,N,P,R,S,T) = 17 unconfigured. **PASS.**

---

## Audit 4: Bridge Prompts

| prompt_key       | Referenced by action? | In prompts.yml? | Headline extracted? |
|------------------|-----------------------|-----------------|---------------------|
| improve_writing  | I (improve)           | YES (line 3)    | YES                 |
| write_email      | R (write_email)       | YES (line 18)   | YES                 |
| prompt_expand    | E (prompt_expand)     | YES (line 39)   | YES                 |
| fix_grammar      | G (grammar)           | YES (line 55)   | YES                 |
| summarize        | S (summarize)         | YES (line 70)   | YES                 |
| translate_da_en  | D (translate_da_en)   | YES (line 86)   | YES                 |
| translate_en_da  | N (translate_en_da)   | YES (line 101)  | YES                 |
| stt_postprocess  | (STT L3 internal)     | YES (line 116)  | YES                 |

**PASS: All 8 prompt templates verified. No orphaned prompts, no missing references.**

---

## Audit 5: Snippet Catalog

| #  | Name                          | Category      | In snippets.yml? |
|----|-------------------------------|---------------|-------------------|
| 1  | Expand this properly          | Prompting     | YES (line 4)      |
| 2  | Improve this prompt           | Prompting     | YES (line 17)     |
| 3  | Write this email              | Email         | YES (line 32)     |
| 4  | Reply to this email           | Email         | YES (line 51)     |
| 5  | Follow up on this             | Email         | YES (line 68)     |
| 6  | Explain this like I'm 10      | Explanation   | YES (line 85)     |
| 7  | Make this concise             | Writing       | YES (line 98)     |
| 8  | Improve the writing           | Writing       | YES (line 110)    |
| 9  | Make this more formal         | Writing       | YES (line 123)    |
| 10 | Make this more natural        | Writing       | YES (line 136)    |
| 11 | Summarize the key points      | Analysis      | YES (line 149)    |
| 12 | Extract action items          | Analysis      | YES (line 161)    |
| 13 | Turn this into meeting notes  | Analysis      | YES (line 176)    |
| 14 | Write a decision memo         | Analysis      | YES (line 189)    |
| 15 | Review this code              | Code          | YES (line 206)    |
| 16 | Explain this code             | Code          | YES (line 222)    |
| 17 | Turn this into a bug report   | Code          | YES (line 235)    |
| 18 | Refactor this code            | Code          | YES (line 249)    |
| 19 | Write tests for this          | Code          | YES (line 263)    |
| 20 | Translate Danish to English   | Translation   | YES (line 275)    |
| 21 | Translate English to Danish   | Translation   | YES (line 287)    |
| 22 | Brainstorm strong options     | Creative      | YES (line 299)    |

**PASS: All 22 snippets verified in extraction map and source file.**

---

## Audit 6: Coordinate Space Allocation

### Width Check

| Element                    | Chars Required | Coordinate Allocated | Status |
|----------------------------|----------------|----------------------|--------|
| Left outer key (row 1-2)   | 13             | cols 5-17            | PASS   |
| Left 5 main keys           | 5 × 13 = 65   | cols 18-82           | PASS   |
| Left encoder               | 10             | cols 83-92           | PASS   |
| Center gap                 | 20             | cols 93-112          | PASS   |
| Right encoder              | 10             | cols 113-122         | PASS   |
| Right 5 main keys          | 5 × 13 = 65   | cols 123-187         | PASS   |
| Right outer key (row 1-2)  | 13             | cols 188-200         | PASS   |
| Right margin               | 4              | cols 201-204         | PASS   |
| **Total**                  | **204**        | **< 380 budget**     | **PASS** |

### Height Check

| Section                    | Lines Required | Lines Allocated  | Status |
|----------------------------|----------------|------------------|--------|
| Header                     | 5              | 1-5              | PASS   |
| 5 layer blocks             | 68             | 8-75             | PASS   |
| Command mode               | 10             | 78-87            | PASS   |
| Encoders/overrides/boot    | 8              | 90-97            | PASS   |
| Snippet catalog            | 14             | 100-113          | PASS   |
| **Total**                  | **~113**       | **≈ 110 target** | **PASS** (tight) |

### Key-to-Coordinate Mapping (spot check)

| Key  | Layer 0 Label | X Start | Y Start | Fits in cell? |
|------|---------------|---------|---------|---------------|
| L11  | "A / GUI"     | 18      | row 1   | 11 chars ✓    |
| R14  | "; / GUI"     | 175     | row 1   | 11 chars ✓    |
| L23  | "C(KC_S)"     | 44      | row 2   | "Ctrl+S" 6ch ✓|
| R04  | "å / Å"       | 175     | row 0   | 5 chars ✓     |
| R34  | "BKSP"        | 148     | thumb   | 4 chars ✓     |

**All spot-checked labels fit within 11-char internal cell width.**

---

## Audit 7: Special Features

| Feature                    | Documented? | Space Allocated? | Status |
|----------------------------|-------------|------------------|--------|
| Home row mods (GACS)       | YES         | YES (in cells)   | PASS   |
| Key override (Shift+Bksp)  | YES         | YES (metadata)   | PASS   |
| Bootloader combo            | YES         | YES (metadata)   | PASS   |
| Autocorrect toggle          | YES         | YES (ADJUST L21) | PASS   |
| Danish Unicode chars        | YES         | YES (RAISE R04,R14,R15) | PASS |
| NAV compose table           | YES         | YES (legend below NAV)  | PASS |
| STT depth levels            | YES         | YES (cmd mode section)  | PASS |
| Column stagger note         | YES         | YES (header note)       | PASS |

---

## Summary

| Audit Category        | Items Checked | Result |
|-----------------------|---------------|--------|
| Key count (5 layers)  | 210           | PASS   |
| Encoder maps          | 20            | PASS   |
| Command mode actions  | 26 (9+17)    | PASS   |
| Bridge prompts        | 8             | PASS   |
| Snippet catalog       | 22            | PASS   |
| Coordinate space      | Width + Height| PASS   |
| Special features      | 8             | PASS   |

**All audits passed. Ready for Phase 5 (ASCII art generation).**
