/* SPDX-License-Identifier: MIT */

#define DT_DRV_COMPAT klor_behavior_unicode

#include <errno.h>
#include <string.h>

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/endpoints.h>
#include <zmk/hid.h>
#include <zmk/hid_indicators.h>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/modifiers.h>

LOG_MODULE_DECLARE(klor_omarchy, CONFIG_ZMK_LOG_LEVEL);

BUILD_ASSERT(IS_ENABLED(CONFIG_ZMK_HID_REPORT_TYPE_HKRO),
             "KLOR Unicode requires the configured 6KRO keyboard report");

/*
 * Local scans, wired split input and behavior timers run on the system work
 * queue in this wired-only port. Keep this short sequence synchronous so a
 * physical key cannot interleave with Linux's Unicode input. USB completion
 * runs independently. In particular, do not unregister held modifiers: ZMK
 * counts their owners, and its mod-morph mask is independent of those counts.
 * Only replace the outgoing report temporarily, then restore it unchanged.
 */
static int unicode_report(const struct zmk_hid_keyboard_report *saved, uint8_t modifiers,
                          uint8_t key) {
    struct zmk_hid_keyboard_report *report = zmk_hid_get_keyboard_report();
    *report = *saved;
    report->body.modifiers = modifiers;
    if (key) {
        /* Keep already-held ordinary keys down. Like QMK, a Unicode digit
         * already physically held cannot produce another key-down edge. */
        bool already_down = false;
        for (size_t i = 0; i < ARRAY_SIZE(report->body.keys); i++) {
            already_down |= report->body.keys[i] == key;
        }
        if (!already_down) {
            for (size_t i = 0; i < ARRAY_SIZE(report->body.keys); i++) {
                if (!report->body.keys[i]) {
                    report->body.keys[i] = key;
                    break;
                }
            }
        }
    }
    int err = zmk_endpoint_send_report(HID_USAGE_KEY);
    k_msleep(10);
    return err;
}

static int unicode_tap(const struct zmk_hid_keyboard_report *saved, uint8_t modifiers,
                       uint8_t key) {
    int err = unicode_report(saved, modifiers, key);
    int release_err = unicode_report(saved, 0, 0);
    return err < 0 ? err : release_err;
}

static int on_unicode_pressed(struct zmk_behavior_binding *binding,
                              struct zmk_behavior_binding_event event) {
    ARG_UNUSED(event);
    struct zmk_hid_keyboard_report *report = zmk_hid_get_keyboard_report();
    const struct zmk_hid_keyboard_report saved = *report;
    bool shifted = saved.body.modifiers & (MOD_LSFT | MOD_RSFT);
    bool caps = zmk_hid_indicators_get_current_profile() & BIT(1);
    uint32_t codepoint = shifted ^ caps ? binding->param2 : binding->param1;

    if (codepoint > 0x10FFFF || (codepoint >= 0xD800 && codepoint <= 0xDFFF)) {
        return -EINVAL;
    }

    bool free_slot = false;
    for (size_t i = 0; i < ARRAY_SIZE(saved.body.keys); i++) {
        free_slot |= saved.body.keys[i] == 0;
    }
    if (!free_slot) {
        LOG_WRN("Unicode needs one free 6KRO report slot");
        return ZMK_BEHAVIOR_OPAQUE;
    }

    /* Linux needs Caps Lock temporarily off, as in QMK's Unicode mode. */
    int err = unicode_report(&saved, 0, 0);
    if (caps) {
        err |= unicode_tap(&saved, 0, HID_USAGE_KEY_KEYBOARD_CAPS_LOCK);
    }
    err |= unicode_tap(&saved, MOD_LCTL | MOD_LSFT, HID_USAGE_KEY_KEYBOARD_U);

    /* QMK register_hex32 emits at least four digits, including leading zeros. */
    bool started = false;
    for (int nibble = 5; nibble >= 0; nibble--) {
        uint8_t digit = (codepoint >> (4 * nibble)) & 0xF;
        if (!started && digit == 0 && nibble >= 4) {
            continue;
        }
        started = true;
        uint8_t key = digit == 0   ? HID_USAGE_KEY_KEYBOARD_0_AND_RIGHT_PARENTHESIS
                      : digit < 10 ? HID_USAGE_KEY_KEYBOARD_1_AND_EXCLAMATION + digit - 1
                                   : HID_USAGE_KEY_KEYBOARD_A + digit - 10;
        err |= unicode_tap(&saved, 0, key);
    }
    /* QMK's Linux mode commits with Space (GTK also accepts Enter). */
    err |= unicode_tap(&saved, 0, HID_USAGE_KEY_KEYBOARD_SPACEBAR);
    if (caps) {
        err |= unicode_tap(&saved, 0, HID_USAGE_KEY_KEYBOARD_CAPS_LOCK);
    }

    *report = saved;
    err |= zmk_endpoint_send_report(HID_USAGE_KEY);
    if (err < 0) {
        LOG_WRN("Unicode report could not be delivered: %d", err);
    }
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_unicode_released(struct zmk_behavior_binding *binding,
                               struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api unicode_driver_api = {
    .binding_pressed = on_unicode_pressed,
    .binding_released = on_unicode_released,
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
};

#define KLOR_UNICODE_INST(n)                                                                       \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, NULL, POST_KERNEL,                                \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &unicode_driver_api);

DT_INST_FOREACH_STATUS_OKAY(KLOR_UNICODE_INST)
