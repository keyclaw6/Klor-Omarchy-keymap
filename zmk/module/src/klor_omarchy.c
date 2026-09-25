/*
 * KLOR Omarchy ZMK compatibility layer.
 *
 * Keeps the existing QMK bridge protocol and stateful keyboard behaviors while
 * using ZMK for the keymap and split transport. Autocorrect is intentionally
 * absent.
 *
 * SPDX-License-Identifier: MIT
 */

#define DT_DRV_COMPAT klor_behavior_control

#include <errno.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/util.h>

#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/hid.h>
#include <zmk/keymap.h>

#include <dt-bindings/zmk/hid_usage.h>
#include <dt-bindings/zmk/hid_usage_pages.h>
#include <dt-bindings/zmk/modifiers.h>
#include <dt-bindings/klor/control.h>

#include <klor/bridge.h>

#if IS_ENABLED(CONFIG_KLOR_OMARCHY_RAW_HID)
#include <zephyr/usb/class/usb_hid.h>
#endif

LOG_MODULE_REGISTER(klor_omarchy, CONFIG_ZMK_LOG_LEVEL);

#define KLOR_PACKET_SIZE 32
#define KLOR_RALT ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_RIGHTALT)

struct klor_control_config {
    uint8_t command_layer;
    uint8_t training_layer;
    uint8_t lower_layer;
    uint8_t raise_layer;
    uint8_t adjust_layer;
    uint8_t nav_layer;
    uint16_t command_timeout_ms;
    uint16_t ralt_tap_window_ms;
    uint16_t stt_tap_window_ms;
};

static const struct klor_control_config *active_cfg;

static bool command_active;
static bool training_mode;

static bool stt_counting;
static bool stt_session_active;
static uint8_t stt_tap_count;

static bool ralt_held;
static bool ralt_interrupted;
static uint8_t ralt_tap_count;
static int64_t ralt_press_started;
static int64_t ralt_first_tap_at;

static bool training_mod_forwarded[64];

static void command_timeout_work_cb(struct k_work *work);
static void stt_finalize_work_cb(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(command_timeout_work, command_timeout_work_cb);
K_WORK_DELAYABLE_DEFINE(stt_finalize_work, stt_finalize_work_cb);

#if IS_ENABLED(CONFIG_KLOR_OMARCHY_RAW_HID)

static const struct device *raw_hid_dev;
K_SEM_DEFINE(raw_hid_tx_sem, 1, 1);

static const uint8_t raw_hid_report_desc[] = {
    0x06, 0x60, 0xFF, /* Usage Page (Vendor Defined 0xFF60) */
    0x09, 0x61,       /* Usage (0x61) */
    0xA1, 0x01,       /* Collection (Application) */
    0x15, 0x00,       /* Logical Minimum (0) */
    0x26, 0xFF, 0x00, /* Logical Maximum (255) */
    0x75, 0x08,       /* Report Size (8) */
    0x95, 0x20,       /* Report Count (32) */
    0x09, 0x62,       /* Usage (0x62) */
    0x81, 0x02,       /* Input (Data,Var,Abs) */
    0x95, 0x20,       /* Report Count (32) */
    0x09, 0x63,       /* Usage (0x63) */
    0x91, 0x02,       /* Output (Data,Var,Abs) */
    0xC0              /* End Collection */
};

static void raw_hid_in_ready(const struct device *dev) { k_sem_give(&raw_hid_tx_sem); }

static void raw_hid_out_ready(const struct device *dev) {
    uint8_t packet[KLOR_PACKET_SIZE] = {0};
    uint32_t read = 0;

    if (hid_int_ep_read(dev, packet, sizeof(packet), &read) < 0 || read == 0) {
        return;
    }

    if (read < KLOR_PACKET_SIZE) {
        memset(packet + read, 0, KLOR_PACKET_SIZE - read);
    }

    if (packet[0] >= 0x20 && packet[0] <= 0x3F) {
        switch (packet[0]) {
        case KLOR_CMD_STATUS:
        case KLOR_CMD_HEARTBEAT:
        case KLOR_CMD_CONFIG:
            packet[1] = 0x01;
            break;
        default:
            packet[1] = 0x00;
            break;
        }

        (void)klor_bridge_send_packet(packet);
    }
}

static const struct hid_ops raw_hid_ops = {
    .int_in_ready = raw_hid_in_ready,
    .int_out_ready = raw_hid_out_ready,
};

int klor_bridge_send_packet(const uint8_t packet[KLOR_PACKET_SIZE]) {
    if (raw_hid_dev == NULL) {
        return -ENODEV;
    }

    if (k_sem_take(&raw_hid_tx_sem, K_MSEC(20)) < 0) {
        return -EBUSY;
    }

    uint32_t written = 0;
    int ret = hid_int_ep_write(raw_hid_dev, packet, KLOR_PACKET_SIZE, &written);
    if (ret < 0 || written != KLOR_PACKET_SIZE) {
        k_sem_give(&raw_hid_tx_sem);
        return ret < 0 ? ret : -EIO;
    }

    return 0;
}

static int raw_hid_init(void) {
    raw_hid_dev = device_get_binding(CONFIG_USB_HID_DEVICE_NAME "_1");
    if (raw_hid_dev == NULL) {
        LOG_ERR("HID_1 not found; KLOR bridge disabled");
        return -ENODEV;
    }

    usb_hid_register_device(raw_hid_dev, raw_hid_report_desc, sizeof(raw_hid_report_desc),
                            &raw_hid_ops);
    int ret = usb_hid_init(raw_hid_dev);
    if (ret < 0) {
        LOG_ERR("Failed to initialize KLOR Raw HID: %d", ret);
        return ret;
    }

    LOG_INF("KLOR QMK-compatible Raw HID ready on HID_1");
    return 0;
}

/* ZMK registers HID_0 at priority 95 and enables USB at 96. */
SYS_INIT(raw_hid_init, APPLICATION, 94);

#else

int klor_bridge_send_packet(const uint8_t packet[KLOR_PACKET_SIZE]) {
    ARG_UNUSED(packet);
    return -ENOTSUP;
}

#endif

int klor_bridge_send_action(uint8_t action_id, uint8_t param) {
    uint8_t packet[KLOR_PACKET_SIZE] = {0};
    packet[0] = KLOR_CMD_ACTION;
    packet[1] = action_id;
    packet[2] = param;
    return klor_bridge_send_packet(packet);
}

static void command_deactivate(void) {
    if (active_cfg != NULL) {
        (void)zmk_keymap_layer_deactivate(active_cfg->command_layer, false);
    }
    command_active = false;
    k_work_cancel_delayable(&command_timeout_work);
}

static void stop_stt_and_exit(void) {
    if (stt_session_active || stt_counting) {
        (void)klor_bridge_send_action(KLOR_ACTION_STT, 0);
    }

    stt_counting = false;
    stt_tap_count = 0;
    stt_session_active = false;
    k_work_cancel_delayable(&stt_finalize_work);
    command_deactivate();
}

static void command_activate(const struct klor_control_config *cfg) {
    active_cfg = cfg;
    command_active = true;
    (void)zmk_keymap_layer_activate(cfg->command_layer, false);
    k_work_reschedule(&command_timeout_work, K_MSEC(cfg->command_timeout_ms));
}

static void command_timeout_work_cb(struct k_work *work) {
    ARG_UNUSED(work);

    if (command_active && !stt_counting && !stt_session_active) {
        command_deactivate();
    }
}

static void stt_finalize(void) {
    if (!stt_counting || active_cfg == NULL) {
        return;
    }

    uint8_t depth = CLAMP(stt_tap_count, 1, 3);
    (void)klor_bridge_send_action(KLOR_ACTION_STT, depth);
    stt_counting = false;
    stt_tap_count = 0;

    stt_session_active = !stt_session_active;
    if (stt_session_active) {
        k_work_cancel_delayable(&command_timeout_work);
    } else {
        command_deactivate();
    }
}

static void stt_finalize_work_cb(struct k_work *work) {
    ARG_UNUSED(work);
    stt_finalize();
}

static uint32_t ascii_action_to_key(uint8_t action) {
    if (action < 0x41 || action > 0x5A) {
        return 0;
    }

    return ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_A + (action - 0x41));
}

static void tap_encoded(uint32_t encoded, int64_t timestamp) {
    if (encoded == 0) {
        return;
    }

    (void)raise_zmk_keycode_state_changed_from_encoded(encoded, true, timestamp);
    (void)raise_zmk_keycode_state_changed_from_encoded(encoded, false, timestamp);
}

static void passthrough_custom_press(int64_t timestamp) {
    ARG_UNUSED(timestamp);

    if (!command_active) {
        return;
    }

    if (stt_counting) {
        stt_finalize();
        return;
    }

    if (stt_session_active) {
        stop_stt_and_exit();
        return;
    }

    command_deactivate();
}

static int handle_bridge_action(uint8_t action, int64_t timestamp) {
    if (stt_counting) {
        /*
         * QMK finalizes the pending STT tap count, then lets the different
         * letter pass through normally instead of dispatching a second action.
         */
        stt_finalize();
        tap_encoded(ascii_action_to_key(action), timestamp);
        return ZMK_BEHAVIOR_OPAQUE;
    }

    if (stt_session_active) {
        (void)klor_bridge_send_action(KLOR_ACTION_STT, 0);
        stt_session_active = false;
    }

    (void)klor_bridge_send_action(action, 0);
    command_deactivate();
    return ZMK_BEHAVIOR_OPAQUE;
}

static int handle_stt_press(void) {
    if (active_cfg == NULL) {
        return ZMK_BEHAVIOR_OPAQUE;
    }

    if (stt_session_active) {
        (void)klor_bridge_send_action(KLOR_ACTION_STT, 0);
        stt_session_active = false;
        command_deactivate();
        return ZMK_BEHAVIOR_OPAQUE;
    }

    if (!stt_counting) {
        stt_counting = true;
        stt_tap_count = 1;
    } else if (stt_tap_count < 3) {
        stt_tap_count++;
    }

    if (stt_tap_count >= 3) {
        k_work_cancel_delayable(&stt_finalize_work);
        stt_finalize();
    } else {
        k_work_reschedule(&stt_finalize_work, K_MSEC(active_cfg->stt_tap_window_ms));
    }

    return ZMK_BEHAVIOR_OPAQUE;
}

static int handle_ralt(bool pressed, struct zmk_behavior_binding_event event,
                       const struct klor_control_config *cfg) {
    active_cfg = cfg;

    if (pressed) {
        if (stt_counting) {
            stt_finalize();
        }

        if (stt_session_active) {
            stop_stt_and_exit();
            ralt_tap_count = 0;
            return ZMK_BEHAVIOR_OPAQUE;
        }

        if (command_active) {
            command_deactivate();
        }

        ralt_held = true;
        ralt_interrupted = false;
        ralt_press_started = event.timestamp;

        if (!training_mode) {
            (void)raise_zmk_keycode_state_changed_from_encoded(KLOR_RALT, true, event.timestamp);
        }

        return ZMK_BEHAVIOR_OPAQUE;
    }

    ralt_held = false;
    if (!training_mode) {
        (void)raise_zmk_keycode_state_changed_from_encoded(KLOR_RALT, false, event.timestamp);
    }

    if (ralt_interrupted || event.timestamp - ralt_press_started > cfg->ralt_tap_window_ms) {
        ralt_tap_count = 0;
        return ZMK_BEHAVIOR_OPAQUE;
    }

    if (ralt_tap_count > 0 &&
        event.timestamp - ralt_first_tap_at <= cfg->ralt_tap_window_ms) {
        ralt_tap_count = 0;
        command_activate(cfg);
        return ZMK_BEHAVIOR_OPAQUE;
    }

    ralt_tap_count = 1;
    ralt_first_tap_at = event.timestamp;
    return ZMK_BEHAVIOR_OPAQUE;
}

static uint32_t nav_key_for_direction(uint32_t dir) {
    switch (dir) {
    case KLOR_NAV_LEFT:
        return ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_LEFTARROW);
    case KLOR_NAV_DOWN:
        return ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_DOWNARROW);
    case KLOR_NAV_UP:
        return ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_UPARROW);
    case KLOR_NAV_RIGHT:
        return ZMK_HID_USAGE(HID_USAGE_KEY, HID_USAGE_KEY_KEYBOARD_RIGHTARROW);
    default:
        return 0;
    }
}

static void handle_nav(uint32_t dir, int64_t timestamp) {
    uint8_t mods = zmk_hid_get_explicit_mods();
    bool shift = mods & (MOD_LSFT | MOD_RSFT);
    bool ctrl = mods & (MOD_LCTL | MOD_RCTL);
    bool alt = mods & (MOD_LALT | MOD_RALT);
    uint32_t arrow = nav_key_for_direction(dir);

    if (arrow == 0) {
        return;
    }

    if (ctrl && alt && !shift && (dir == KLOR_NAV_LEFT || dir == KLOR_NAV_RIGHT)) {
        tap_encoded(LC(LG(arrow)), timestamp);
        return;
    }

    if (ctrl && !shift && !alt) {
        switch (dir) {
        case KLOR_NAV_LEFT:
            tap_encoded(LG(ZMK_HID_USAGE(HID_USAGE_KEY,
                                         HID_USAGE_KEY_KEYBOARD_MINUS_AND_UNDERSCORE)),
                        timestamp);
            return;
        case KLOR_NAV_RIGHT:
            tap_encoded(LG(ZMK_HID_USAGE(HID_USAGE_KEY,
                                         HID_USAGE_KEY_KEYBOARD_EQUAL_AND_PLUS)),
                        timestamp);
            return;
        case KLOR_NAV_UP:
            tap_encoded(LS(LG(ZMK_HID_USAGE(HID_USAGE_KEY,
                                            HID_USAGE_KEY_KEYBOARD_MINUS_AND_UNDERSCORE))),
                        timestamp);
            return;
        case KLOR_NAV_DOWN:
            tap_encoded(LS(LG(ZMK_HID_USAGE(HID_USAGE_KEY,
                                            HID_USAGE_KEY_KEYBOARD_EQUAL_AND_PLUS))),
                        timestamp);
            return;
        }
    }

    if (shift && alt) {
        tap_encoded(LS(LA(LG(arrow))), timestamp);
    } else if (shift) {
        tap_encoded(LS(LG(arrow)), timestamp);
    } else if (alt) {
        tap_encoded(LA(LG(arrow)), timestamp);
    } else {
        tap_encoded(LG(arrow), timestamp);
    }
}

static bool training_modifier_should_forward(const struct klor_control_config *cfg) {
    if (zmk_keymap_layer_active(cfg->nav_layer)) {
        return false;
    }

    return zmk_keymap_layer_active(cfg->lower_layer) ||
           zmk_keymap_layer_active(cfg->raise_layer) ||
           zmk_keymap_layer_active(cfg->adjust_layer);
}

static int on_control_pressed(struct zmk_behavior_binding *binding,
                              struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct klor_control_config *cfg = dev->config;
    active_cfg = cfg;

    switch (binding->param1) {
    case KLOR_CTRL_ACTION:
        return handle_bridge_action((uint8_t)binding->param2, event.timestamp);

    case KLOR_CTRL_STT:
        return handle_stt_press();

    case KLOR_CTRL_RALT:
        return handle_ralt(true, event, cfg);

    case KLOR_CTRL_TRAIN_TOGGLE:
        training_mode = !training_mode;
        if (training_mode) {
            (void)zmk_keymap_layer_activate(cfg->training_layer, false);
        } else {
            (void)zmk_keymap_layer_deactivate(cfg->training_layer, false);
        }
        return ZMK_BEHAVIOR_OPAQUE;

    case KLOR_CTRL_TRAIN_MOD: {
        passthrough_custom_press(event.timestamp);
        bool forward = training_modifier_should_forward(cfg);
        if (event.position < ARRAY_SIZE(training_mod_forwarded)) {
            training_mod_forwarded[event.position] = forward;
        }
        if (forward) {
            (void)raise_zmk_keycode_state_changed_from_encoded(binding->param2, true,
                                                               event.timestamp);
        }
        return ZMK_BEHAVIOR_OPAQUE;
    }

    case KLOR_CTRL_NAV:
        passthrough_custom_press(event.timestamp);
        handle_nav(binding->param2, event.timestamp);
        return ZMK_BEHAVIOR_OPAQUE;

    default:
        return -ENOTSUP;
    }
}

static int on_control_released(struct zmk_behavior_binding *binding,
                               struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct klor_control_config *cfg = dev->config;

    switch (binding->param1) {
    case KLOR_CTRL_RALT:
        return handle_ralt(false, event, cfg);

    case KLOR_CTRL_TRAIN_MOD:
        if (event.position < ARRAY_SIZE(training_mod_forwarded) &&
            training_mod_forwarded[event.position]) {
            training_mod_forwarded[event.position] = false;
            (void)raise_zmk_keycode_state_changed_from_encoded(binding->param2, false,
                                                               event.timestamp);
        }
        return ZMK_BEHAVIOR_OPAQUE;

    default:
        return ZMK_BEHAVIOR_OPAQUE;
    }
}

static int keycode_listener(const zmk_event_t *eh) {
    const struct zmk_keycode_state_changed *ev = as_zmk_keycode_state_changed(eh);
    if (ev == NULL || !ev->state) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    bool is_ralt = ev->usage_page == HID_USAGE_KEY &&
                   ev->keycode == HID_USAGE_KEY_KEYBOARD_RIGHTALT;

    if (ralt_held && !is_ralt) {
        ralt_interrupted = true;
        ralt_tap_count = 0;
    }

    if (!command_active || is_ralt) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (stt_counting) {
        stt_finalize();
        return ZMK_EV_EVENT_BUBBLE;
    }

    if (stt_session_active) {
        stop_stt_and_exit();
    } else {
        command_deactivate();
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(klor_command_listener, keycode_listener);
ZMK_SUBSCRIPTION(klor_command_listener, zmk_keycode_state_changed);

static const struct behavior_driver_api klor_control_driver_api = {
    .binding_pressed = on_control_pressed,
    .binding_released = on_control_released,
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
};

#define KLOR_CONTROL_INST(n)                                                                        \
    static const struct klor_control_config klor_control_config_##n = {                             \
        .command_layer = DT_INST_PROP(n, command_layer),                                            \
        .training_layer = DT_INST_PROP(n, training_layer),                                          \
        .lower_layer = DT_INST_PROP(n, lower_layer),                                                \
        .raise_layer = DT_INST_PROP(n, raise_layer),                                                \
        .adjust_layer = DT_INST_PROP(n, adjust_layer),                                              \
        .nav_layer = DT_INST_PROP(n, nav_layer),                                                    \
        .command_timeout_ms = DT_INST_PROP(n, command_timeout_ms),                                  \
        .ralt_tap_window_ms = DT_INST_PROP(n, ralt_tap_window_ms),                                  \
        .stt_tap_window_ms = DT_INST_PROP(n, stt_tap_window_ms),                                    \
    };                                                                                              \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, &klor_control_config_##n, POST_KERNEL,             \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &klor_control_driver_api);

DT_INST_FOREACH_STATUS_OKAY(KLOR_CONTROL_INST)
