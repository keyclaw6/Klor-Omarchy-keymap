#include "stubs.h"
#include KLOR_CONTROL_SOURCE

#define KEY(usage) ZMK_HID_USAGE(HID_USAGE_KEY, usage)
#define BIND(dev, a, b) ((struct zmk_behavior_binding){dev, a, b})
static const struct klor_control_config config = {
    .nav_layer = 4,
    .command_timeout_ms = 3000,
    .ralt_tap_window_ms = 350,
    .stt_tap_window_ms = 300,
};
static struct zmk_behavior_binding pressed_bindings[44];
static unsigned status_callbacks;
static void original_usb_status(struct usb_cfg_data *cfg, enum usb_dc_status_code status,
                                const uint8_t *param) {
    (void)cfg;
    (void)status;
    (void)param;
    status_callbacks++;
}

static void flush_usb(void) {
    do {
        raw_hid_in_ready(&usb_device);
    } while (raw_hid_tx_queue.count);
}
static void reset_state(void) {
    command_active = training_mode = stt_counting = stt_session_active = false;
    ralt_held = ralt_interrupted = ralt_forwarded = false;
    stt_tap_count = ralt_tap_count = 0;
    ralt_press_started = ralt_first_tap_at = 0;
    memset(consumed, 0, sizeof consumed);
    memset(training_forwarded, 0, sizeof training_forwarded);
    memset(active_layers, 0, sizeof active_layers);
    active_layers[0] = true;
    memset(pressed_bindings, 0, sizeof pressed_bindings);
    for (unsigned l = 0; l < 5; l++)
        for (unsigned p = 0; p < 44; p++)
            layers[l][p] = BIND(l ? "trans" : "none", 0, 0);
    layers[0][40] = BIND("klor_ctrl", KLOR_CTRL_RALT, 0);
    key_count = packet_count = 0;
    explicit_mods = 0;
    now = 10000;
    command_timeout_work.pending = stt_finalize_work.pending = false;
    raw_hid_tx_queue = (struct msgq){0};
    raw_hid_tx_sem.count = 1;
    control_device.config = &config;
    status_callbacks = 0;
    incoming_length = 32;
    usb_config.cb_usb_status = original_usb_status;
    usb_interface.bInterfaceSubClass = 1;
    usb_device.config = &usb_config;
    assert(control_init(&control_device) == 0);
    assert(raw_hid_init() == 0);
}
static void time_passes(int64_t ms) {
    int64_t target = now + ms;
    for (;;) {
        struct k_work_delayable *first = NULL;
        struct k_work_delayable *timers[] = {&command_timeout_work, &stt_finalize_work};
        for (unsigned i = 0; i < 2; i++)
            if (timers[i]->pending && timers[i]->due <= target &&
                (!first || timers[i]->due < first->due))
                first = timers[i];
        if (!first)
            break;
        now = first->due;
        first->pending = false;
        first->work.handler(&first->work);
        flush_usb();
    }
    now = target;
}
static int physical(unsigned position, bool down) {
    struct zmk_position_state_changed ev = {
        .source = 255, .position = position, .state = down, .timestamp = now};
    int result = position_listener(&ev);
    if (result == ZMK_EV_EVENT_BUBBLE) {
        struct zmk_behavior_binding binding;
        if (down) {
            const struct zmk_behavior_binding *resolved = binding_at(position);
            binding = resolved ? *resolved : BIND("none", 0, 0);
            pressed_bindings[position] = binding;
        } else
            binding = pressed_bindings[position];
        struct zmk_behavior_binding_event event = {
            .position = position, .source = 255, .timestamp = now};
        if (binding.behavior_dev && !strcmp(binding.behavior_dev, "klor_ctrl")) {
            if (down)
                on_control_pressed(&binding, event);
            else
                on_control_released(&binding, event);
        } else if (binding.behavior_dev && !strcmp(binding.behavior_dev, "kp")) {
            raise_zmk_keycode_state_changed_from_encoded(binding.param1, down, now);
        } else if (binding.behavior_dev && !strcmp(binding.behavior_dev, "mo")) {
            if (down)
                zmk_keymap_layer_activate(binding.param1, false);
            else
                zmk_keymap_layer_deactivate(binding.param1, false);
        }
    }
    flush_usb();
    return result;
}
static void tap(unsigned position) {
    physical(position, true);
    time_passes(10);
    physical(position, false);
    time_passes(10);
}
static void assert_action(unsigned index, uint8_t action, uint8_t depth) {
    assert(index < packet_count && packets[index][0] == 0x20 && packets[index][1] == action &&
           packets[index][2] == depth);
    for (unsigned i = 3; i < 32; i++)
        assert(!packets[index][i]);
}
static void enter_command(void) {
    tap(40);
    time_passes(30);
    tap(40);
    assert(command_active);
    key_count = 0;
}

static void test_training(void) {
    unsigned mods[] = {224, 225, 226, 227};
    for (unsigned layer = 0; layer < 5; layer++)
        for (unsigned train = 0; train < 2; train++)
            for (unsigned m = 0; m < 4; m++) {
                reset_state();
                active_layers[layer] = true;
                training_mode = train;
                layers[0][36] = BIND("klor_ctrl", KLOR_CTRL_TRAIN_MOD, KEY(mods[m]));
                physical(36, true);
                bool forward = !train || (layer != 0 && layer != 4);
                assert(key_count == (forward ? 1u : 0u));
                if (forward)
                    assert(keys[0].key == KEY(mods[m]) && keys[0].down);
                /* Release owns the press decision despite a mode/layer change. */
                training_mode = !train;
                active_layers[4] = true;
                physical(36, false);
                assert(key_count == (forward ? 2u : 0u));
                if (forward)
                    assert(!keys[1].down && keys[1].key == KEY(mods[m]));
            }
    for (unsigned layer = 0; layer < 5; layer++)
        for (unsigned train = 0; train < 2; train++) {
            reset_state();
            active_layers[layer] = true;
            training_mode = train;
            layers[0][35] = BIND("klor_ctrl", KLOR_CTRL_DIRECT_NAV, 0);
            physical(35, true);
            if (!train)
                assert(active_layers[4]);
            else
                assert(active_layers[4] == (layer == 4));
            training_mode = !train;
            physical(35, false);
            assert(active_layers[4] == (train && layer == 4));
        }
    reset_state();
    training_mode = true;
    layers[0][11] = BIND("hml", KEY(227), KEY(4));
    layers[0][15] = BIND("nav_l", 4, KEY(10));
    assert(physical(11, true) == ZMK_EV_EVENT_BUBBLE);
    assert(physical(15, true) == ZMK_EV_EVENT_BUBBLE);
    enter_command();
    assert(key_count == 0); /* RALT taps survive training without Alt output. */
    puts("PASS training: all layers/modifiers, transparent thumbs, held releases, direct NAV, "
         "HRM/GH, RALT");
}

static void test_command(void) {
    const char *wrappers[] = {"kp", "hml", "hmr", "hml_fast", "hmr_fast", "nav_l", "nav_r"};
    for (unsigned w = 0; w < ARRAY_SIZE(wrappers); w++)
        for (unsigned letter = 0; letter < 26; letter++) {
            reset_state();
            layers[0][0] = BIND(wrappers[w], w ? 4 : KEY(4 + letter), w ? KEY(4 + letter) : 0);
            command_activate(&config);
            assert(physical(0, true) == ZMK_EV_EVENT_HANDLED);
            if (letter == 19) {
                assert(stt_counting && !packet_count);
                time_passes(300);
                assert_action(0, 0x10, 1);
            } else {
                assert(!command_active);
                assert_action(0, 0x41 + letter, 0);
            }
            active_layers[1] = true;
            layers[1][0] = BIND("kp", KEY(30), 0);
            assert(physical(0, false) == ZMK_EV_EVENT_HANDLED);
            assert(!key_count);
        }
    struct zmk_behavior_binding unmapped[] = {
        BIND("kp", KEY(82), 0),
        BIND("kp", LC(KEY(22)), 0),
        BIND("none", 0, 0),
        BIND("mo", 1, 0),
        BIND("bootloader", 0, 0),
        BIND("klor_unicode", 0xe5, 0xc5),
        BIND("bspc_del", 0, 0),
        BIND("klor_ctrl", KLOR_CTRL_TRAIN_TOGGLE, 0),
        BIND("klor_ctrl", KLOR_CTRL_NAV, KLOR_NAV_LEFT),
    };
    for (unsigned i = 0; i < ARRAY_SIZE(unmapped); i++) {
        reset_state();
        layers[0][0] = BIND("kp", KEY(4), 0);
        active_layers[1] = true;
        layers[1][0] = unmapped[i];
        command_activate(&config);
        assert(physical(0, true) == ZMK_EV_EVENT_BUBBLE);
        assert(!command_active && !packet_count);
        assert(physical(0, false) == ZMK_EV_EVENT_BUBBLE);
    }
    for (unsigned session = 0; session < 3; session++) {
        reset_state();
        layers[0][10] = BIND("kp", KEY(41), 0); /* ESC */
        command_activate(&config);
        stt_counting = session == 1;
        stt_tap_count = stt_counting ? 1 : 0;
        stt_session_active = session == 2;
        if (stt_counting)
            k_work_reschedule(&stt_finalize_work, 300);

        int press_result = physical(10, true);
        if (session == 1) {
            /* QMK finalizes the T depth first, then lets ESC pass through. */
            assert(press_result == ZMK_EV_EVENT_BUBBLE);
            assert(command_active && !stt_counting && stt_session_active);
            assert_action(0, 0x10, 1);
            assert(key_count == 1 && keys[0].down);
            assert(physical(10, false) == ZMK_EV_EVENT_BUBBLE);
            assert(key_count == 2 && !keys[1].down);
        } else {
            assert(press_result == ZMK_EV_EVENT_HANDLED);
            assert(!command_active && !stt_counting && !stt_session_active && !key_count);
            assert(physical(10, false) == ZMK_EV_EVENT_HANDLED);
            if (session == 2)
                assert_action(0, 0x10, 0);
            else
                assert(packet_count == 0);
        }
        time_passes(310);
        assert(packet_count == (session ? 1u : 0u));
    }
    reset_state();
    command_activate(&config);
    time_passes(2999);
    assert(command_active);
    time_passes(1);
    assert(!command_active);
    reset_state();
    layers[0][36] = BIND("klor_ctrl", KLOR_CTRL_TRAIN_MOD, KEY(224));
    physical(36, true);
    command_activate(&config);
    physical(36, false);
    assert(key_count == 2 && !keys[1].down); /* A mode switch must not strand an earlier key. */
    puts("PASS command: 26 letters x7 behavior types, current layer, all unmapped kinds, QMK "
         "ESC/counting order, timeout, release pairing");
}

static void test_stt(void) {
    for (unsigned depth = 1; depth <= 3; depth++) {
        reset_state();
        layers[0][4] = BIND("kp", KEY(23), 0);
        enter_command();
        for (unsigned i = 0; i < depth; i++)
            tap(4);
        if (depth < 3) {
            assert(packet_count == 0);
            time_passes(300);
        } else
            assert(packet_count == 1);
        assert_action(0, 0x10, depth);
        assert(command_active && stt_session_active && !stt_counting);
        time_passes(4000);
        assert(command_active);
        for (unsigned i = 0; i < depth; i++)
            tap(4);
        if (depth < 3) {
            assert(packet_count == 1);
            time_passes(300);
        } else
            assert(packet_count == 2);
        assert_action(1, 0x10, depth);
        assert(!command_active && !stt_session_active && !key_count);
    }
    reset_state();
    layers[0][4] = BIND("kp", KEY(23), 0);
    layers[0][11] = BIND("hml", KEY(227), KEY(4));
    enter_command();
    tap(4);
    assert(physical(11, true) == ZMK_EV_EVENT_BUBBLE);
    assert_action(0, 0x10, 1);
    assert(stt_session_active && command_active && !consumed[11]);
    assert(!strcmp(pressed_bindings[11].behavior_dev, "hml"));
    assert(physical(11, false) == ZMK_EV_EVENT_BUBBLE);
    assert(!key_count);
    time_passes(400);
    assert(packet_count == 1);
    layers[0][0] = BIND("kp", KEY(4), 0);
    tap(0);
    assert_action(1, 0x10, 0);
    assert_action(2, 'A', 0);
    assert(!command_active);
    puts("PASS STT: depths1/2/3 start and stop,300ms timer, active timeout exemption, HRM "
         "passthrough, stop-before-action");
}

static void test_ralt(void) {
    reset_state();
    enter_command();
    assert(ralt_tap_count == 0);
    const struct zmk_behavior_binding interruptors[] = {
        BIND("none", 0, 0), BIND("mo", 1, 0), BIND("hml", KEY(224), KEY(7)), BIND("kp", KEY(4), 0)};
    for (unsigned i = 0; i < ARRAY_SIZE(interruptors); i++) {
        reset_state();
        layers[0][0] = interruptors[i];
        physical(40, true);
        tap(0);
        physical(40, false);
        assert(!command_active && !ralt_tap_count && ralt_interrupted);
        reset_state();
        layers[0][0] = interruptors[i];
        tap(40);
        assert(ralt_tap_count == 1);
        tap(0);
        assert(ralt_tap_count == 0);
        tap(40);
        assert(!command_active && ralt_tap_count == 1);
    }
    reset_state();
    physical(40, true);
    time_passes(351);
    physical(40, false);
    assert(!ralt_tap_count);
    reset_state();
    tap(40);
    time_passes(351);
    tap(40);
    assert(!command_active);
    reset_state();
    physical(40, true);
    training_mode = true;
    physical(40, false);
    assert(key_count == 2 && keys[0].down && !keys[1].down);
    reset_state();
    training_mode = true;
    physical(40, true);
    training_mode = false;
    physical(40, false);
    assert(!key_count);
    reset_state();
    layers[0][4] = BIND("kp", KEY(23), 0);
    enter_command();
    tap(4);
    time_passes(300);
    physical(40, true);
    assert_action(1, 0x10, 0);
    assert(!stt_session_active && !command_active);
    physical(40, false);
    puts("PASS RALT: completed taps,350ms bounds, all position interruptors, pending tap "
         "cancellation, matching releases, STT stop");
}

static void test_nav(void) {
    unsigned directions[] = {KLOR_NAV_LEFT, KLOR_NAV_DOWN, KLOR_NAV_UP, KLOR_NAV_RIGHT};
    unsigned arrows[] = {80, 81, 82, 79};
    for (unsigned hand = 0; hand < 2; hand++)
        for (unsigned mods = 0; mods < 8; mods++)
            for (unsigned d = 0; d < 4; d++) {
                reset_state();
                bool ctrl = mods & 1, shift = mods & 2, alt = mods & 4;
                explicit_mods = (ctrl ? (hand ? MOD_RCTL : MOD_LCTL) : 0) |
                                (shift ? (hand ? MOD_RSFT : MOD_LSFT) : 0) |
                                (alt ? (hand ? MOD_RALT : MOD_LALT) : 0);
                uint8_t before = explicit_mods;
                uint32_t expected = LG(KEY(arrows[d]));
                if (ctrl && alt && !shift && (d == 0 || d == 3))
                    expected = LC(expected);
                else if (ctrl && !shift && !alt)
                    expected = (d == 0   ? LG(KEY(45))
                                : d == 3 ? LG(KEY(46))
                                : d == 2 ? LS(LG(KEY(45)))
                                         : LS(LG(KEY(46))));
                else if (shift && alt)
                    expected = LS(LA(expected));
                else if (shift)
                    expected = LS(expected);
                else if (alt)
                    expected = LA(expected);
                handle_nav(directions[d], now);
                assert(key_count == 2 && keys[0].key == expected && keys[0].down &&
                       keys[1].key == expected && !keys[1].down);
                assert(explicit_mods ==
                       before); /* Held Ctrl/Alt remain alongside emitted GUI/Shift/Alt. */
            }
    puts("PASS NAV:64 directional/modifier cases, left/right held modifiers preserved");
}

static void test_raw_hid(void) {
    reset_state();
    assert(descriptor_size == sizeof(raw_hid_report_desc));
    assert(usb_interface.bInterfaceSubClass == 0);
    const uint8_t expected[] = {0x06, 0x60, 0xff, 0x09, 0x61, 0xa1, 0x01, 0x15, 0x00,
                                0x26, 0xff, 0x00, 0x75, 0x08, 0x95, 0x20, 0x09, 0x62,
                                0x81, 0x02, 0x95, 0x20, 0x09, 0x63, 0x91, 0x02, 0xc0};
    assert(descriptor_size == sizeof expected && !memcmp(descriptor, expected, sizeof expected));
    unsigned commands[] = {0x21, 0x22, 0x23, 0x20, 0x3f, 0x1f, 0x40};
    for (unsigned c = 0; c < ARRAY_SIZE(commands); c++) {
        unsigned before = packet_count;
        for (unsigned b = 0; b < 32; b++)
            incoming[b] = b + 64;
        incoming[0] = commands[c];
        raw_hid_out_ready(&usb_device);
        flush_usb();
        if (commands[c] < 0x20 || commands[c] > 0x3f) {
            assert(packet_count == before);
            continue;
        }
        assert(packet_count == before + 1 && packets[before][0] == commands[c]);
        assert(packets[before][1] == (commands[c] >= 0x21 && commands[c] <= 0x23));
        assert(!memcmp(packets[before] + 2, incoming + 2, 30));
    }
    reset_state();
    raw_hid_tx_sem.count = 0;
    for (unsigned i = 0; i < 16; i++)
        assert(klor_bridge_send_action('A' + i, i) == 0);
    assert(!packet_count && klor_bridge_send_action('Z', 0) == -ENOSPC);
    flush_usb();
    assert(packet_count == 16);
    for (unsigned i = 0; i < 16; i++)
        assert_action(i, 'A' + i, i);
    for (unsigned status = USB_DC_RESET; status <= USB_DC_ERROR; status++) {
        reset_state();
        assert(klor_bridge_send_action('A', 0) == 0 && packet_count == 1 &&
               raw_hid_tx_sem.count == 0);
        assert(klor_bridge_send_action('B', 0) == 0 && raw_hid_tx_queue.count == 1);
        usb_config.cb_usb_status(&usb_config, status, NULL);
        assert(status_callbacks == 1 && raw_hid_tx_queue.count == 0 && raw_hid_tx_sem.count == 1);
        assert(klor_bridge_send_action('C', 0) == 0 && packet_count == 2);
        assert_action(1, 'C', 0); /* No stale B replay after reconnect. */
    }
    reset_state();
    incoming_length = 1;
    incoming[0] = 0x22;
    raw_hid_out_ready(&usb_device);
    flush_usb();
    assert(packet_count == 1 && packets[0][0] == 0x22 && packets[0][1] == 1);
    for (unsigned i = 2; i < 32; i++)
        assert(!packets[0][i]);
    incoming_length = 0;
    raw_hid_out_ready(&usb_device);
    assert(packet_count == 1);
    puts("PASS Raw HID: exact no-ID32byte descriptor, status/heartbeat/config ACK, NACK/ignore, "
         "packet tail, FIFO/backpressure, disconnect recovery");
}

int main(int argc, char **argv) {
    assert(argc == 2);
    if (!strcmp(argv[1], "training"))
        test_training();
    else if (!strcmp(argv[1], "command"))
        test_command();
    else if (!strcmp(argv[1], "stt"))
        test_stt();
    else if (!strcmp(argv[1], "ralt"))
        test_ralt();
    else if (!strcmp(argv[1], "nav"))
        test_nav();
    else if (!strcmp(argv[1], "raw_hid"))
        test_raw_hid();
    else
        return 2;
    return 0;
}
