#!/usr/bin/env python3
"""Compare every port position with the untouched QMK main-branch reference."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


def arguments(text):
    parts, start, depth = [], 0, 0
    for i, char in enumerate(text):
        depth += (char == '(') - (char == ')')
        if char == ',' and depth == 0:
            parts.append(text[start:i].strip())
            start = i + 1
    parts.append(text[start:].strip())
    return parts


def qmk_layers():
    text = subprocess.check_output([
        'git', 'show', 'main:keyboards/geigeigeist/klor/keymaps/plain/keymap.c'
    ], cwd=ROOT, text=True)
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    result = []
    for match in re.finditer(r'\[(_\w+)\]\s*=\s*LAYOUT_polydactyl\(', text):
        start, end, depth = match.end(), match.end(), 1
        while depth:
            depth += (text[end] == '(') - (text[end] == ')')
            end += 1
        result.append((match[1], arguments(text[start:end - 1])))
    return result


ALIASES = dict(zip(
    'QUOT COMM SLSH SPC ENT LCTL LSFT EQL LCBR RCBR PPLS RGHT LBRC RBRC '
    'MINS UNDS PSCR PGUP PGDN LPRN RPRN PAST EXLM DLR PERC CIRC AMPR BSLS GRV '
    'MUTE MPLY APP'.split(),
    'SQT COMMA FSLH SPACE ENTER LCTRL LSHFT EQUAL LBRC RBRC KP_PLUS RIGHT LBKT RBKT '
    'MINUS UNDER PSCRN PG_UP PG_DN LPAR RPAR KP_MULTIPLY EXCL DLLR PRCNT CARET AMPS BSLH GRAVE '
    'C_MUTE C_PP K_APP'.split()))
MODS = {'LALT': 'LA', 'RALT': 'RA', 'LSFT': 'LS', 'LGUI': 'LG',
        'LCTL': 'LC', 'C': 'LC', 'S': 'LS', 'A': 'LA', 'G': 'LG', 'LSG': 'LS_LG'}


def keycode(qmk):
    if qmk.startswith('KC_'):
        key = qmk[3:]
        return 'N' + key if key.isdigit() else ALIASES.get(key, key)
    match = re.fullmatch(r'(\w+)\((.*)\)', qmk)
    assert match and match[1] in MODS, qmk
    mod = MODS[match[1]]
    key = keycode(match[2])
    return 'LS(LG(' + key + '))' if mod == 'LS_LG' else mod + '(' + key + ')'


def binding(qmk):
    specials = {
        '_______': '&trans', 'XXXXXXX': '&none', 'AC_TOGG': '&none',
        'QK_BOOT': '&bootloader', 'KC_BSPC': '&bspc_del',
        'TL_LOWR': '&mo LOWER', 'TL_UPPR': '&mo RAISE',
        'MO(_NAV)': '&klor_ctrl KLOR_CTRL_DIRECT_NAV 0',
        'TRAIN_TOGG': '&klor_ctrl KLOR_CTRL_TRAIN_TOGGLE 0',
        'KC_RALT': '&klor_ctrl KLOR_CTRL_RALT 0',
        'HRM_A': '&hml LGUI A', 'HRM_S': '&hml LALT S',
        'HRM_D': '&hml_fast LCTRL D', 'HRM_F': '&hml_fast LSHFT F',
        'HRM_J': '&hmr_fast RSHFT J', 'HRM_K': '&hmr_fast RCTRL K',
        'HRM_L': '&hmr LALT L', 'HRM_SCLN': '&hmr RGUI SEMI',
        'LT_G_NAV': '&nav_l NAV G', 'LT_H_NAV': '&nav_r NAV H',
    }
    if qmk in specials:
        return specials[qmk]
    if qmk in ('KC_LGUI', 'KC_LCTL', 'KC_LSFT', 'KC_LALT'):
        return '&klor_ctrl KLOR_CTRL_TRAIN_MOD ' + keycode(qmk)
    if qmk.startswith('NAV_'):
        return '&klor_ctrl KLOR_CTRL_NAV KLOR_' + qmk
    if qmk.startswith('UP('):
        letter = re.search(r'U_(AA|AE|OE)_L', qmk)[1]
        return '&unicode ' + {'AA': '0x00e5 0x00c5', 'AE': '0x00e6 0x00c6',
                              'OE': '0x00f8 0x00d8'}[letter]
    return '&kp ' + keycode(qmk)


class KeymapParity(unittest.TestCase):
    def test_all_220_positions_against_qmk(self):
        text = (ROOT / 'zmk/config/klor.keymap').read_text()
        layers = re.findall(r'(\w+)_layer\s*\{\s*bindings\s*=\s*<(.*?)>;', text, re.S)
        self.assertEqual([name for name, _ in layers], ['base', 'lower', 'raise', 'adjust', 'nav'])
        reference = qmk_layers()
        self.assertEqual(len(reference), 5)
        for (qmk_name, keys), (name, bindings) in zip(reference, layers):
            actual = [' '.join(item.split()) for item in re.findall(r'&[^&]+', bindings)]
            self.assertEqual(len(keys), 44, qmk_name)
            self.assertEqual(len(actual), 44, name)
            for position, (key, found) in enumerate(zip(keys, actual)):
                with self.subTest(layer=name, position=position, qmk=key):
                    self.assertEqual(binding(key), found)

    def test_chordal_exemptions_and_speculative_scope(self):
        text = (ROOT / 'zmk/config/klor.keymap').read_text()
        exempt = {28, 29, *range(36, 44)}
        left = set(range(5)) | set(range(10, 16)) | set(range(22, 28))
        right = set(range(5, 10)) | set(range(16, 22)) | set(range(30, 36))
        for label in ['hml', 'hmr', 'hml_fast', 'hmr_fast', 'nav_l', 'nav_r']:
            block = re.search(r'\b' + label + r':[^\{]+\{(.*?)\};', text, re.S)[1]
            positions = {int(n) for n in re.search(r'hold-trigger-key-positions\s*=\s*<(.*?)>',
                                                  block, re.S)[1].split()}
            opposite = right if label in ('hml', 'hml_fast', 'nav_l') else left
            self.assertEqual(positions, exempt | opposite, label)
            self.assertEqual('hold-while-undecided;' in block, label.endswith('_fast'))
            for prop, value in [('tapping-term-ms', 180), ('quick-tap-ms', 0),
                                ('require-prior-idle-ms', 120)]:
                self.assertRegex(block, prop + r'\s*=\s*<' + str(value) + '>')


if __name__ == '__main__':
    unittest.main()
