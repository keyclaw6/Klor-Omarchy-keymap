/* SPDX-License-Identifier: MIT */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/retention/bootmode.h>
#include <zephyr/sys/reboot.h>

#include <zmk/event_manager.h>
#include <zmk/events/position_state_changed.h>

LOG_MODULE_REGISTER(klor_boot, CONFIG_ZMK_LOG_LEVEL);

/*
 * QMK compatibility: pressing all four thumbs on one half together five times
 * within three seconds enters that half's UF2 bootloader. Only LOCAL position
 * events count, so the central never reboots because of the other half and an
 * isolated peripheral can still enter its own bootloader.
 */
#define KLOR_BOOT_COMBO_WINDOW_MS 3000
#define KLOR_BOOT_COMBO_COUNT 5

static bool boot_thumb_down[8];
static bool boot_combo_held;
static uint8_t boot_combo_count;
static int64_t boot_combo_started;

static int thumb_slot(uint32_t position) {
    if (position >= 36 && position <= 43) {
        return (int)(position - 36);
    }

    return -1;
}

static bool thumb_group_all_down(int first) {
    return boot_thumb_down[first] && boot_thumb_down[first + 1] && boot_thumb_down[first + 2] &&
           boot_thumb_down[first + 3];
}

static int boot_combo_listener(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = as_zmk_position_state_changed(eh);
    if (ev == NULL || ev->source != ZMK_POSITION_STATE_CHANGE_SOURCE_LOCAL) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    int slot = thumb_slot(ev->position);
    if (slot < 0) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    boot_thumb_down[slot] = ev->state;
    bool all_down = thumb_group_all_down(0) || thumb_group_all_down(4);

    if (all_down && !boot_combo_held) {
        boot_combo_held = true;

        if (boot_combo_count == 0 ||
            ev->timestamp - boot_combo_started > KLOR_BOOT_COMBO_WINDOW_MS) {
            boot_combo_count = 1;
            boot_combo_started = ev->timestamp;
        } else {
            boot_combo_count++;
        }

        if (boot_combo_count >= KLOR_BOOT_COMBO_COUNT) {
            int ret = bootmode_set(BOOT_MODE_TYPE_BOOTLOADER);
            if (ret < 0) {
                LOG_ERR("Failed to set UF2 boot mode: %d", ret);
                boot_combo_count = 0;
                return ZMK_EV_EVENT_BUBBLE;
            }

            sys_reboot(SYS_REBOOT_WARM);
        }
    } else if (!all_down && boot_combo_held) {
        boot_combo_held = false;
    }

    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(klor_boot_combo_listener, boot_combo_listener);
ZMK_SUBSCRIPTION(klor_boot_combo_listener, zmk_position_state_changed);
