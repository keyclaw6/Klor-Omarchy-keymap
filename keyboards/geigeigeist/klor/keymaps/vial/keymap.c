/*
 * ZYNEX GROUP - Klor Keyboard Firmware (Vial)
 * Custom keymap for Raspberry Pi Pico 2040
 * Wired split, 42-key Polydactyl layout
 *
 * Vial-compatible version: uses standard QMK keycodes so all keys
 * are remappable through the Vial GUI.
 *
 * Changes from zynex keymap:
 *   - LOWER/RAISE custom keycodes → MO() + TRI_LAYER_ENABLE
 *   - SNAP2 custom keycode → QK_KB_0 (visible in Vial as "SNAP2")
 *   - COMBO_COUNT removed (Vial manages combos dynamically)
 *   - encoder_update_user → encoder_map (Vial-remappable)
 *   - OLED code removed (not installed on this board)
 *   - Danish characters (æ ø å) via hold-to-activate on P/;/' and Unicode Map on RAISE
 *   - One-shot shift on left thumb (OSM(MOD_LSFT))
 *   - HRM_SCLN replaced with DK_SC_AE (æ on hold, RGUI via cross-hand chord)
 */

#include QMK_KEYBOARD_H
#include "klor.h"
#include "raw_hid.h"

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ D E F I N I T I O N S                                                                                                                      │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// ┌───────────────────────────────────────────────────────────┐
// │ h o m e   r o w   m o d s   ( G A C S )                   │
// └───────────────────────────────────────────────────────────┘

// Left hand: GUI / ALT / CTL / SFT (pinky → index)
#define HRM_A  LGUI_T(KC_A)
#define HRM_S  LALT_T(KC_S)
#define HRM_D  LCTL_T(KC_D)
#define HRM_F  LSFT_T(KC_F)

// Right hand: SFT / CTL / ALT (index → ring)
// NOTE: HRM_L uses LALT (not RALT) to avoid AltGr conflicts on the RAISE layer
// NOTE: Pinky (;) is now DK_SC_AE (Danish æ on hold) — RGUI removed from home row
#define HRM_J    RSFT_T(KC_J)
#define HRM_K    RCTL_T(KC_K)
#define HRM_L    LALT_T(KC_L)

// ┌───────────────────────────────────────────────────────────┐
// │ d e f i n e   l a y e r s                                 │
// └───────────────────────────────────────────────────────────┘

enum klor_layers {
    _QWERTY,
    _LOWER,
    _RAISE,
    _ADJUST,
    _NAV,
};

// ┌───────────────────────────────────────────────────────────┐
// │ c u s t o m   k e y c o d e s   ( V i a l - v i s i b l e ) │
// └───────────────────────────────────────────────────────────┘

// Use QK_KB_0 instead of SAFE_RANGE so Vial can see/assign these keycodes
enum custom_keycodes {
    SNAP2 = QK_KB_0,
    DK_P_AA,    // Tap = P,    Hold = å/Å
    DK_SC_AE,   // Tap = ;,    Hold = æ/Æ  (replaces HRM_SCLN / RGUI)
    DK_QT_OE,   // Tap = ',    Hold = ø/Ø
};

// ┌───────────────────────────────────────────────────────────┐
// │ b r i d g e   p r o t o c o l   ( R a w   H I D )         │
// └───────────────────────────────────────────────────────────┘

// Command IDs: our protocol uses 0x20–0x3F (VIA uses 0x01–0x0F)
#define CMD_BRIDGE_ACTION    0x20  // byte[1] = action_id, byte[2] = param
#define CMD_BRIDGE_STATUS    0x21  // host → keyboard: byte[1] = status_code
#define CMD_BRIDGE_HEARTBEAT 0x22  // bidirectional ping
#define CMD_BRIDGE_CONFIG    0x23  // byte[1] = config_key, bytes[2+] = value

// Action IDs (sent as byte[1] of CMD_BRIDGE_ACTION)
// ASCII uppercase scheme: each letter A-Z maps to its ASCII code (0x41-0x5A).
// The bridge daemon's actions.yml decides what each letter does.
// To assign a new action, just add an entry in actions.yml — no firmware change needed.
#define ACTION_STT          0x10  // Special: byte[2] = depth (1-3), triggered by T key

// ┌───────────────────────────────────────────────────────────┐
// │ u n i c o d e   m a p   ( D a n i s h   æ ø å )           │
// └───────────────────────────────────────────────────────────┘

enum unicode_names {
    U_AA_L,  // å  U+00E5
    U_AA_U,  // Å  U+00C5
    U_AE_L,  // æ  U+00E6
    U_AE_U,  // Æ  U+00C6
    U_OE_L,  // ø  U+00F8
    U_OE_U,  // Ø  U+00D8
};

const uint32_t PROGMEM unicode_map[] = {
    [U_AA_L] = 0x00E5,  // å
    [U_AA_U] = 0x00C5,  // Å
    [U_AE_L] = 0x00E6,  // æ
    [U_AE_U] = 0x00C6,  // Æ
    [U_OE_L] = 0x00F8,  // ø
    [U_OE_U] = 0x00D8,  // Ø
};

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ K E Y M A P S                                                                                                                              │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {

 /*
   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸

   ┌───────────────────────────────────────────────────────────┐
   │ q w e r t y   ( h o m e   r o w   m o d s )               │
   └───────────────────────────────────────────────────────────┘
             ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
             │    Q    │    W    │    E    │    R    │    T    │ ╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮ │    Y    │    U    │    I    │    O    │  P / å  │
   ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │╰╯╰╯╰╯╰╯╰╯╰╯╰╯╰╯│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
   │   TAB   │  GUI/A  │  ALT/S  │  CTL/D  │  SFT/F  │    G    ├─╯                ╰─┤    H    │  SFT/J  │  CTL/K  │  ALT/L  │  ; / æ  │  ' / ø  │
   ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
   │ CMD/WIN │    Z    │    X    │    C    │    V    │    B    ││  MUTE  ││PLY/PSE ││    N    │    M    │    ,    │    .    │    /    │   NAV   │
   └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┼─────────┴─────────┴─────────┘
                                  │  CTRL   │  LOWER  │  SPACE  │OSM SHFT ││  R ALT  │  ENTER  │  RAISE  │ BSPACE  │
                                  └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘ */

   [_QWERTY] = LAYOUT_polydactyl(
 //╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷
              KC_Q,     KC_W,     KC_E,     KC_R,     KC_T,                          KC_Y,     KC_U,     KC_I,     KC_O,     DK_P_AA,
    KC_TAB,   HRM_A,    HRM_S,    HRM_D,    HRM_F,    KC_G,                          KC_H,     HRM_J,    HRM_K,    HRM_L,    DK_SC_AE, DK_QT_OE,
    KC_LGUI,  KC_Z,     KC_X,     KC_C,     KC_V,     KC_B,     KC_MUTE,   KC_MPLY,  KC_N,     KC_M,     KC_COMM,  KC_DOT,   KC_SLSH,  MO(_NAV),
                                  KC_LCTL,  MO(_LOWER),KC_SPC,  OSM(MOD_LSFT), KC_RALT,  KC_ENT,   MO(_RAISE),KC_BSPC
 ),

 /*
   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸

   ┌───────────────────────────────────────────────────────────┐
   │ l o w e r                                                 │
   └───────────────────────────────────────────────────────────┘
             ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
             │ CAPSLCK │  HOME   │    ↑    │    =    │    {    │ ╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮ │    }    │    7    │    8    │    9    │    +    │
   ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │╰╯╰╯╰╯╰╯╰╯╰╯╰╯╰╯│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
   │   ESC   │   DEL   │    ←    │    ↓    │    →    │    [    ├─╯                ╰─┤    ]    │    4    │    5    │    6    │    -    │    _    │
   ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
   │ SCRNSHT │   END   │   PG↑   │  SAVE   │   PG↓   │    (    ││  MUTE  ││PLY/PSE ││    )    │    1    │    2    │    3    │    *    │    ▼    │
   └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┼─────────┴─────────┴─────────┘
                                 │    ▼    │    ▼    │    ▼    │    ▼    ││    ▼    │    ▼    │    ▼    │    0    │
                                 └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘ */

   [_LOWER] = LAYOUT_polydactyl(
 //╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷
              KC_CAPS,  KC_HOME,  KC_UP,    KC_EQL,   KC_LCBR,                       KC_RCBR,  KC_7,    KC_8,    KC_9,    KC_PPLS,
    KC_ESC,   KC_DEL,   KC_LEFT,  KC_DOWN,  KC_RGHT,  KC_LBRC,                       KC_RBRC,  KC_4,    KC_5,    KC_6,    KC_MINS,  KC_UNDS,
    SNAP2,    KC_END,   KC_PGUP,  C(KC_S),  KC_PGDN,  KC_LPRN,  KC_MUTE,   KC_MPLY,  KC_RPRN,  KC_1,    KC_2,    KC_3,    KC_PAST,  _______,
                                  _______,  _______,  _______,  _______,   _______,  _______,  _______,  KC_0
 ),

 /*
   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸

   ┌───────────────────────────────────────────────────────────┐
   │ r a i s e                                                 │
   └───────────────────────────────────────────────────────────┘
             ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
             │    !    │    @    │    #    │    $    │    %    │ ╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮ │    ^    │    &    │    \    │    °    │   å/Å   │
   ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │╰╯╰╯╰╯╰╯╰╯╰╯╰╯╰╯│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
   │  AF13   │  AF14   │  AF15   │  AF16   │  AF17   │   SZ    ├─╯                ╰─┤    ¥    │    €    │    £    │    ≈    │   æ/Æ   │   ø/Ø   │
   ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
   │  AF18   │  AF19   │  AF20   │  AF21   │  AF22   │  AF23   ││  MUTE  ││PLY/PSE ││    ≤    │    ≥    │   CUE   │    ~    │    `    │    ▼    │
   └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┼─────────┴─────────┴─────────┘
                                 │    ▼    │    ▼    │    ▼    │    ▼    ││    ▼    │    ▼    │    ▼    │    ▼    │
                                 └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘ */

   [_RAISE] = LAYOUT_polydactyl(
 //╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷
              KC_EXLM,  KC_AT,    KC_HASH,  KC_DLR,   KC_PERC,                       KC_CIRC,  KC_AMPR,  KC_BSLS,RALT(KC_3),UP(U_AA_L, U_AA_U),
  LALT(KC_F13),LALT(KC_F14),LALT(KC_F15),LALT(KC_F16),LALT(KC_F17),RALT(KC_S),      RALT(KC_Y),RALT(KC_5),RALT(KC_4),RALT(KC_EQL),  UP(U_AE_L, U_AE_U), UP(U_OE_L, U_OE_U),
  LALT(KC_F18),LALT(KC_F19),LALT(KC_F20),LALT(KC_F21),LALT(KC_F22),LALT(KC_F23),KC_MUTE,KC_MPLY,RALT(KC_COMM),RALT(KC_DOT),  RALT(KC_C), LSFT(KC_GRV),   KC_GRV,  _______,
                                  _______,  _______,  _______,  _______,   _______,  _______,  _______,  _______
 ),

 /*
   ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸

   ┌───────────────────────────────────────────────────────────┐
   │ a d j u s t                                               │
   └───────────────────────────────────────────────────────────┘
             ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
             │   F15   │   F16   │   F17   │   F18   │   F19   │ ╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮ │         │   F7    │   F8    │   F9    │   F14   │
   ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │╰╯╰╯╰╯╰╯╰╯╰╯╰╯╰╯│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
   │   F20   │   F21   │   F22   │   F23   │   F24   │   APP   ├─╯                ╰─┤         │   F4    │   F5    │   F6    │   F12   │   F13   │
   ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
   │  RESET  │         │         │         │         │         ││  MUTE  ││PLY/PSE ││         │   F1    │   F2    │   F3    │   F10   │   F11   │
   └─────────┴─────────┴─────────┼─────────┼─────────┼─────────┼╰────────╯╰────────╯┼─────────┼─────────┼─────────┴─────────┴─────────┴─────────┘
                                 │    ▼    │    ▼    │    ▼    │    ▼    ││    ▼    │    ▼    │    ▼    │ BSPACE  │
                                 └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘
*/

   [_ADJUST] = LAYOUT_polydactyl(
 //╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷
              KC_F15,   KC_F16,   KC_F17,   KC_F18,   KC_F19,                        XXXXXXX,  KC_F7,    KC_F8,    KC_F9,    KC_F14,
    KC_F20,   KC_F21,   KC_F22,   KC_F23,   KC_F24,   KC_APP,                        XXXXXXX,  KC_F4,    KC_F5,    KC_F6,    KC_F12,   KC_F13,
    QK_BOOT,  XXXXXXX,  XXXXXXX,  XXXXXXX,  XXXXXXX,  XXXXXXX,  KC_MUTE,   KC_MPLY,  XXXXXXX,  KC_F1,    KC_F2,    KC_F3,    KC_F10,   KC_F11,
                                  _______,  _______,  _______,  _______,   _______,  _______,  _______,  KC_BSPC
 ),

 /*
    ╺━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╸

    ┌───────────────────────────────────────────────────────────┐
    │ n a v   ( H y p r l a n d   w i n d o w   m a n a g e r ) │
    └───────────────────────────────────────────────────────────┘
              ┌─────────┬─────────┬─────────┬─────────┬─────────┐                    ┌─────────┬─────────┬─────────┬─────────┬─────────┐
              │         │         │  GUI+↑  │         │         │ ╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮╭╮ │         │  GUI+7  │  GUI+8  │  GUI+9  │         │
    ┌─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤ │╰╯╰╯╰╯╰╯╰╯╰╯╰╯╰╯│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┐
    │ GUI+TAB │         │  GUI+←  │  GUI+↓  │  GUI+→  │         ├─╯                ╰─┤         │  GUI+4  │  GUI+5  │  GUI+6  │         │         │
    ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤╭────────╮╭────────╮├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
    │         │         │         │         │         │         ││  MUTE  ││PLY/PSE ││         │  GUI+1  │  GUI+2  │  GUI+3  │         │         │
    └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┤│        ││        │├─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
                                  │         │         │         │         ││         │         │         │  GUI+0  │
                                  └─────────┴─────────┴─────────┴─────────┘└─────────┴─────────┴─────────┴─────────┘
 */

   [_NAV] = LAYOUT_polydactyl(
 //╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷╷         ╷         ╷         ╷         ╷         ╷         ╷         ╷
             _______,  _______,  LGUI(KC_UP), _______, _______,                      _______,  LGUI(KC_7), LGUI(KC_8), LGUI(KC_9), _______,
   LGUI(KC_TAB), _______,  LGUI(KC_LEFT), LGUI(KC_DOWN), LGUI(KC_RGHT), _______,     _______,  LGUI(KC_4), LGUI(KC_5), LGUI(KC_6), _______,  _______,
   _______,  _______,  _______,  _______,  _______,  _______,  _______,   _______,    _______,  LGUI(KC_1), LGUI(KC_2), LGUI(KC_3), _______,  _______,
                                   _______,  _______,  _______,  _______,   _______,  _______,  _______,  LGUI(KC_0)
  ),
};

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ C H O R D A L   H O L D   L A Y O U T                                                                                                      │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// 'L' = left hand, 'R' = right hand, '*' = thumb / exempt (allows same-hand thumb+mod chords)
const char chordal_hold_layout[MATRIX_ROWS][MATRIX_COLS] PROGMEM =
    LAYOUT_polydactyl(
        'L', 'L', 'L', 'L', 'L',                     'R', 'R', 'R', 'R', 'R',
        'L', 'L', 'L', 'L', 'L', 'L',                'R', 'R', 'R', 'R', 'R', 'R',
        'L', 'L', 'L', 'L', 'L', 'L', '*', '*',      'R', 'R', 'R', 'R', 'R', 'R',
                            '*', '*', '*', '*',        '*', '*', '*', '*'
    );

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ E N C O D E R   M A P   ( V i a l - r e m a p p a b l e )                                                                                  │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

#if defined(ENCODER_MAP_ENABLE)
const uint16_t PROGMEM encoder_map[][NUM_ENCODERS][NUM_DIRECTIONS] = {
    [_QWERTY] = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU), ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [_LOWER]  = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU), ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [_RAISE]  = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU), ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [_ADJUST] = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU), ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
    [_NAV]    = { ENCODER_CCW_CW(KC_VOLD, KC_VOLU), ENCODER_CCW_CW(KC_VOLD, KC_VOLU) },
};
#endif

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ D A N I S H   H O L D - T O - A C T I V A T E                                                                                              │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// Hold P → å, Hold ; → æ, Hold ' → ø (same tapping term as HRM: 200ms)
// Shift-aware: if shift is held when the hold threshold fires, output Å/Æ/Ø instead.

typedef struct {
    uint16_t timer;
    bool     pressed;
    bool     resolved;    // true once hold output has been sent
    bool     used_as_mod; // true if DK_SC_AE was resolved as RGUI (cross-hand chord)
} dk_hold_state_t;

static dk_hold_state_t dk_states[3] = {{0}};

// Codepoints indexed by dk_states[] index: [lower, upper]
static const uint32_t dk_codepoints[3][2] = {
    {0x00E5, 0x00C5},  // å / Å  (P key, idx=0)
    {0x00E6, 0x00C6},  // æ / Æ  (; key, idx=1)
    {0x00F8, 0x00D8},  // ø / Ø  (' key, idx=2)
};

// Tap keycodes indexed by dk_states[] index
static const uint16_t dk_tap_kc[3] = {KC_P, KC_SCLN, KC_QUOT};

// Returns index 0-2 if keycode is a Danish hold key, or -1 otherwise.
static int8_t dk_index(uint16_t keycode) {
    switch (keycode) {
        case DK_P_AA:  return 0;
        case DK_SC_AE: return 1;
        case DK_QT_OE: return 2;
        default:       return -1;
    }
}

static bool process_danish_hold(uint16_t keycode, keyrecord_t *record) {
    int8_t idx = dk_index(keycode);
    if (idx < 0) return true;  // not a Danish key

    if (record->event.pressed) {
        dk_states[idx].timer      = timer_read();
        dk_states[idx].pressed    = true;
        dk_states[idx].resolved   = false;
        dk_states[idx].used_as_mod = false;
        return false;  // defer output until release or hold threshold
    } else {
        dk_states[idx].pressed = false;
        if (dk_states[idx].used_as_mod) {
            // Was resolved as RGUI via cross-hand chord — unregister the modifier
            unregister_code(KC_RGUI);
            dk_states[idx].used_as_mod = false;
        } else if (!dk_states[idx].resolved) {
            // Released before tapping term — it's a tap: send the normal keycode.
            // One-shot shift (if active) is consumed naturally by tap_code16.
            tap_code16(dk_tap_kc[idx]);
        }
        return false;
    }
}

// Resolve any pending holds that crossed the tapping term.
// Called from matrix_scan_user() every matrix cycle (~1ms).
static void dk_hold_tick(void) {
    for (uint8_t i = 0; i < 3; i++) {
        if (dk_states[i].pressed && !dk_states[i].resolved &&
            timer_elapsed(dk_states[i].timer) > TAPPING_TERM) {
            dk_states[i].resolved = true;
            // Check shift state for upper/lower codepoint
            uint8_t mods = get_mods() | get_oneshot_mods();
            bool shifted = mods & MOD_MASK_SHIFT;
            // Temporarily remove shift so register_unicode sends the correct char
            if (shifted) {
                del_mods(MOD_MASK_SHIFT);
                del_oneshot_mods(MOD_MASK_SHIFT);
            }
            register_unicode(dk_codepoints[i][shifted ? 1 : 0]);
            // Restore shift
            if (shifted) {
                set_mods(mods);
            }
        }
    }
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ C O M M A N D   M O D E   ( t r i p l e - t a p   A L T )                                                                                  │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// State machine for the AI bridge command mode.
// Triple-tap right ALT enters command mode. Next keypress dispatches an action
// via Raw HID to the Python bridge daemon.

#define COMMAND_MODE_TIMEOUT 3000  // Exit command mode after 3s of no input
#define STT_TAP_WINDOW       300  // Window for counting T-key taps for STT depth

static bool     cmd_mode_active = false;
static uint16_t cmd_mode_timer  = 0;

// STT tap counting state
static bool     stt_counting    = false;
static uint8_t  stt_tap_count   = 0;
static uint16_t stt_tap_timer   = 0;

// Send a bridge action packet via Raw HID (32 bytes, zero-padded)
static void bridge_send_action(uint8_t action_id, uint8_t param) {
    uint8_t data[32] = {0};
    data[0] = CMD_BRIDGE_ACTION;
    data[1] = action_id;
    data[2] = param;
    raw_hid_send(data, sizeof(data));
}

// Finalize and send the STT action with accumulated tap count
static void stt_finalize(void) {
    if (stt_counting) {
        bridge_send_action(ACTION_STT, stt_tap_count);
        stt_counting  = false;
        stt_tap_count = 0;
        cmd_mode_active = false;
    }
}

// Map a keycode to an action ID during command mode.
// All 26 base-layer letters are mapped to their ASCII uppercase code (0x41-0x5A).
// T key returns 0xFF sentinel to trigger the STT tap-counting path.
// Returns 0 if the key is not a mappable letter.
// Handles mod-tap wrappers (e.g., LGUI_T(KC_A)) by extracting the base keycode.
static uint8_t cmd_action_for_key(uint16_t keycode) {
    // Strip mod-tap / layer-tap wrapper to get the base keycode
    if ((keycode >= QK_MOD_TAP && keycode <= QK_MOD_TAP_MAX) ||
        (keycode >= QK_LAYER_TAP && keycode <= QK_LAYER_TAP_MAX)) {
        keycode = keycode & 0xFF;
    }

    // Also handle Danish hold keys → base letter
    switch (keycode) {
        case DK_P_AA:  return 0x50;  // P
        case DK_SC_AE: return 0;     // semicolon — not a letter, unmapped
        case DK_QT_OE: return 0;     // quote — not a letter, unmapped
        default: break;
    }

    switch (keycode) {
        case KC_A: return 0x41;
        case KC_B: return 0x42;
        case KC_C: return 0x43;
        case KC_D: return 0x44;
        case KC_E: return 0x45;
        case KC_F: return 0x46;
        case KC_G: return 0x47;
        case KC_H: return 0x48;
        case KC_I: return 0x49;
        case KC_J: return 0x4A;
        case KC_K: return 0x4B;
        case KC_L: return 0x4C;
        case KC_M: return 0x4D;
        case KC_N: return 0x4E;
        case KC_O: return 0x4F;
        case KC_P: return 0x50;
        case KC_Q: return 0x51;
        case KC_R: return 0x52;
        case KC_S: return 0x53;
        case KC_T: return 0xFF;  // sentinel: STT uses tap counting, handled separately
        case KC_U: return 0x55;
        case KC_V: return 0x56;
        case KC_W: return 0x57;
        case KC_X: return 0x58;
        case KC_Y: return 0x59;
        case KC_Z: return 0x5A;
        default:   return 0;
    }
}

// Process a keypress while command mode is active.
// Returns false to consume the key, true to pass through.
static bool process_command_mode(uint16_t keycode, keyrecord_t *record) {
    if (!record->event.pressed) return false;  // only act on press

    // If we're in the STT tap-counting window
    if (stt_counting) {
        if (keycode == KC_T) {
            stt_tap_count++;
            if (stt_tap_count >= 3) {
                stt_finalize();  // max depth reached
            } else {
                stt_tap_timer = timer_read();
            }
            return false;
        } else {
            // Different key pressed during STT counting — finalize with current count
            stt_finalize();
            // Fall through to let the key be processed normally
            return true;
        }
    }

    // ESC cancels command mode
    if (keycode == KC_ESC) {
        cmd_mode_active = false;
        return false;
    }

    uint8_t action = cmd_action_for_key(keycode);

    if (action == 0xFF) {
        // T key: start STT tap counting
        stt_counting  = true;
        stt_tap_count = 1;
        stt_tap_timer = timer_read();
        return false;
    }

    if (action > 0) {
        bridge_send_action(action, 0);
        cmd_mode_active = false;
        return false;
    }

    // Unmapped key: exit command mode, pass keypress through
    cmd_mode_active = false;
    return true;
}

// ┌───────────────────────────────────────────────────────────┐
// │ t r i p l e - t a p   R A L T   s t a t e   m a c h i n e │
// └───────────────────────────────────────────────────────────┘

// Manual triple-tap detection for KC_RALT → enter Command Mode.
// Can't use QMK tap_dance_actions[] because Vial owns that array.
// Single/double tap = normal RALT.  Triple tap within window = Command Mode.

#define RALT_TAP_WINDOW  250  // ms window for triple-tap detection

static uint8_t  ralt_tap_count = 0;
static uint16_t ralt_tap_timer = 0;
static bool     ralt_held      = false;

// Called from process_record_user on KC_RALT press/release.
// Returns false to consume the event, true to pass through.
static bool process_ralt_triple_tap(keyrecord_t *record) {
    if (record->event.pressed) {
        ralt_held = true;
        if (ralt_tap_count > 0 && timer_elapsed(ralt_tap_timer) > RALT_TAP_WINDOW) {
            // Window expired — reset count
            ralt_tap_count = 0;
        }
        ralt_tap_count++;
        ralt_tap_timer = timer_read();

        if (ralt_tap_count >= 3) {
            // Triple tap achieved — enter command mode
            ralt_tap_count  = 0;
            cmd_mode_active = true;
            cmd_mode_timer  = timer_read();
            // Don't register ALT for the third tap
            return false;
        }

        // Register ALT normally (will be unregistered on release)
        register_code(KC_RALT);
        return false;
    } else {
        // Release
        ralt_held = false;
        unregister_code(KC_RALT);
        return false;
    }
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ V i a l   +   R a w   H I D   C o e x i s t e n c e                                                                                        │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// Override the weak raw_hid_receive_kb() to intercept our bridge protocol (0x20–0x3F).
// In vial-qmk, via.c's raw_hid_receive() dispatches unknown command IDs to this hook.
// NOTE: Do NOT call raw_hid_send() here — via.c calls it automatically after we return.
//       We only modify data[] in-place; via.c sends the buffer as our response.
void raw_hid_receive_kb(uint8_t *data, uint8_t length) {
    uint8_t command_id = data[0];

    if (command_id >= 0x20 && command_id <= 0x3F) {
        switch (command_id) {
            case CMD_BRIDGE_STATUS:
                // Host sent a status update — acknowledge
                // (future: update LED state, etc.)
                data[1] = 0x01;  // ACK
                break;

            case CMD_BRIDGE_HEARTBEAT:
                // Respond to heartbeat ping
                data[1] = 0x01;  // alive
                break;

            case CMD_BRIDGE_CONFIG:
                // Host sent a config update — acknowledge
                data[1] = 0x01;  // ACK
                break;

            default:
                // Unknown bridge command
                data[1] = 0x00;  // NACK
                break;
        }
        return;  // handled — via.c will send the response
    }

    // Not our command — set unhandled marker (VIA convention)
    data[0] = id_unhandled;
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ M A C R O S                                                                                                                                │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    // ── Command Mode interception (highest priority) ──
    // When active, intercept the next keypress as an action command.
    if (cmd_mode_active) {
        bool pass_through = process_command_mode(keycode, record);
        if (!pass_through) return false;
        // If pass_through is true, command mode exited and key should be processed normally
    }

    // ── Triple-tap RALT → Command Mode ──
    if (keycode == KC_RALT) {
        return process_ralt_triple_tap(record);
    }
    // Any other key pressed resets the RALT tap count
    if (record->event.pressed && ralt_tap_count > 0 && !ralt_held) {
        ralt_tap_count = 0;
    }

    // ── Danish hold-to-activate ──
    if (dk_index(keycode) >= 0) {
        return process_danish_hold(keycode, record);
    }

    // ── If another key is pressed while a Danish key is held (before hold threshold),
    //    resolve pending Danish keys as taps immediately (same as flow-tap behavior).
    //    Exception: DK_SC_AE (idx=1) acts as RGUI when the interrupting key is on the
    //    opposite (left) hand — detected via chordal_hold_layout. ──
    if (record->event.pressed) {
        for (uint8_t i = 0; i < 3; i++) {
            if (dk_states[i].pressed && !dk_states[i].resolved) {
                if (i == 1) {
                    // DK_SC_AE: check which hand the interrupting key is on
                    char hand = pgm_read_byte(&chordal_hold_layout[record->event.key.row][record->event.key.col]);
                    if (hand == 'L') {
                        // Cross-hand chord: resolve as RGUI modifier
                        dk_states[i].resolved   = true;
                        dk_states[i].used_as_mod = true;
                        register_code(KC_RGUI);
                        // Let the interrupting key pass through — it will combine with RGUI
                        continue;
                    }
                }
                // Same-hand or non-DK_SC_AE: resolve as tap
                dk_states[i].resolved = true;
                tap_code16(dk_tap_kc[i]);
            }
        }
    }

    // ── Existing macros ──
    switch (keycode) {
        case SNAP2:
            if (record->event.pressed) {
                SEND_STRING(SS_LSFT(SS_LWIN("S")));
            }
            break;
    }
    return true;
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ B O O T L O A D E R   C O M B O   ( 5 ×   a l l   t h u m b   k e y s )                                                                      │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// Press all 4 thumb keys on one half simultaneously, 5 times in a row, to enter
// UF2 bootloader. Works per-half (each half can enter bootloader independently
// even when disconnected from the other half).
//
// Matrix positions (from LAYOUT_polydactyl macro):
//   Left  thumbs: row 3, cols 1-4 (L31, L32, L33, L34)
//   Right thumbs: row 7, cols 1-4 (R31, R32, R33, R34)

#define BOOT_COMBO_COUNT    5     // Number of all-thumbs presses required
#define BOOT_COMBO_WINDOW   3000  // ms — must complete all 5 within this window

// Left thumb matrix: row 3, cols 1-4
#define LEFT_THUMB_ROW   3
#define LEFT_THUMB_COL0  1
#define LEFT_THUMB_COL3  4

// Right thumb matrix: row 7, cols 1-4
#define RIGHT_THUMB_ROW  7
#define RIGHT_THUMB_COL0 1
#define RIGHT_THUMB_COL3 4

static uint8_t  boot_combo_count  = 0;
static uint16_t boot_combo_timer  = 0;
static bool     boot_combo_held   = false;  // true while all 4 thumbs are currently down

// Check if all 4 thumb keys on either half are currently pressed by reading
// the live key matrix directly. Returns true if all 4 are down on at least
// one half.
static bool all_thumbs_pressed(void) {
    // Check left half (row 3, cols 1-4)
    bool left_all = true;
    for (uint8_t c = LEFT_THUMB_COL0; c <= LEFT_THUMB_COL3; c++) {
        if (!matrix_is_on(LEFT_THUMB_ROW, c)) {
            left_all = false;
            break;
        }
    }
    if (left_all) return true;

    // Check right half (row 7, cols 1-4)
    bool right_all = true;
    for (uint8_t c = RIGHT_THUMB_COL0; c <= RIGHT_THUMB_COL3; c++) {
        if (!matrix_is_on(RIGHT_THUMB_ROW, c)) {
            right_all = false;
            break;
        }
    }
    return right_all;
}

// Called from matrix_scan_user() every ~1ms.
static void boot_combo_tick(void) {
    bool thumbs_down = all_thumbs_pressed();

    if (thumbs_down && !boot_combo_held) {
        // Transition: thumbs just pressed together
        boot_combo_held = true;

        if (boot_combo_count == 0 || timer_elapsed(boot_combo_timer) > BOOT_COMBO_WINDOW) {
            // First press or window expired — restart
            boot_combo_count = 1;
            boot_combo_timer = timer_read();
        } else {
            boot_combo_count++;
        }

        if (boot_combo_count >= BOOT_COMBO_COUNT) {
            // 5 presses achieved — enter bootloader
            reset_keyboard();
        }
    } else if (!thumbs_down && boot_combo_held) {
        // Transition: thumbs released
        boot_combo_held = false;
    }
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ M A T R I X   S C A N   ( p e r i o d i c   t a s k s )                                                                                    │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

void matrix_scan_user(void) {
    // Danish hold-to-activate tick
    dk_hold_tick();

    // Command mode timeout (3 seconds)
    if (cmd_mode_active && !stt_counting &&
        timer_elapsed(cmd_mode_timer) > COMMAND_MODE_TIMEOUT) {
        cmd_mode_active = false;
    }

    // STT tap-counting window timeout (300ms)
    if (stt_counting && timer_elapsed(stt_tap_timer) > STT_TAP_WINDOW) {
        stt_finalize();
    }

    // Bootloader combo: 5× all thumbs on one half
    boot_combo_tick();
}

// ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
// │ T R I - L A Y E R   C O N F I G                                                                                                            │
// └────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

// TRI_LAYER_ENABLE in rules.mk activates ADJUST(3) when LOWER(1) + RAISE(2) are both held.
// Default tri-layer config uses layers 1, 2, 3 which matches our enum exactly.
