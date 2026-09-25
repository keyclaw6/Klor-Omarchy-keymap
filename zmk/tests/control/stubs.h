/* Minimal host doubles for the Zephyr/ZMK APIs used by the real control source. */
#pragma once
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#define IS_ENABLED(x) (x)
#define CONFIG_KLOR_OMARCHY_RAW_HID 1
#define CONFIG_USB_HID_DEVICE_NAME "HID"
#define CONFIG_ZMK_LOG_LEVEL 0
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define ARG_UNUSED(x) ((void)(x))
#define CLAMP(v, lo, hi) ((v) < (lo) ? (lo) : ((v) > (hi) ? (hi) : (v)))
#define LOG_MODULE_REGISTER(...)
#define LOG_DBG(...) ((void)0)
#define LOG_INF(...) ((void)0)
#define LOG_WRN(...) ((void)0)
#define LOG_ERR(...) ((void)0)
#define ZMK_KEYMAP_LEN 44
#define ZMK_KEYMAP_LAYERS_LEN 5
#define ZMK_BEHAVIOR_OPAQUE 0
#define ZMK_EV_EVENT_BUBBLE 0
#define ZMK_EV_EVENT_HANDLED 1
#define BEHAVIOR_LOCALITY_CENTRAL 0
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
#define SYS_INIT(...)
#define DT_INST_FOREACH_STATUS_OKAY(...)
#define STR_INNER(x) #x
#define STR(x) STR_INNER(x)
#define DEVICE_DT_NAME(x) STR(x)
#define DT_NODELABEL(x) x
#define K_MSEC(x) (x)
#define K_NO_WAIT 0

#define HID_USAGE_KEY 7
#define ZMK_HID_USAGE(page, key) (((page) << 16) | (key))
#define HID_USAGE_KEY_KEYBOARD_A 4
#define HID_USAGE_KEY_KEYBOARD_T 23
#define HID_USAGE_KEY_KEYBOARD_Z 29
#define HID_USAGE_KEY_KEYBOARD_ESCAPE 41
#define HID_USAGE_KEY_KEYBOARD_MINUS_AND_UNDERSCORE 45
#define HID_USAGE_KEY_KEYBOARD_EQUAL_AND_PLUS 46
#define HID_USAGE_KEY_KEYBOARD_RIGHTARROW 79
#define HID_USAGE_KEY_KEYBOARD_LEFTARROW 80
#define HID_USAGE_KEY_KEYBOARD_DOWNARROW 81
#define HID_USAGE_KEY_KEYBOARD_UPARROW 82
#define HID_USAGE_KEY_KEYBOARD_LEFTCONTROL 224
#define HID_USAGE_KEY_KEYBOARD_LEFTSHIFT 225
#define HID_USAGE_KEY_KEYBOARD_LEFTALT 226
#define HID_USAGE_KEY_KEYBOARD_LEFT_GUI 227
#define HID_USAGE_KEY_KEYBOARD_RIGHTALT 230
#define MOD_LCTL 1
#define MOD_LSFT 2
#define MOD_LALT 4
#define MOD_LGUI 8
#define MOD_RCTL 16
#define MOD_RSFT 32
#define MOD_RALT 64
#define MOD_RGUI 128
#define LC(k) ((k) | (MOD_LCTL << 24))
#define LS(k) ((k) | (MOD_LSFT << 24))
#define LA(k) ((k) | (MOD_LALT << 24))
#define LG(k) ((k) | (MOD_LGUI << 24))

enum usb_dc_status_code { USB_DC_RESET, USB_DC_DISCONNECTED, USB_DC_ERROR, USB_DC_CONFIGURED };
struct usb_if_descriptor {
    uint8_t bInterfaceSubClass;
};
struct usb_cfg_data {
    struct usb_if_descriptor *interface_descriptor;
    void (*cb_usb_status)(struct usb_cfg_data *, enum usb_dc_status_code, const uint8_t *);
};
static struct usb_if_descriptor usb_interface;
static struct usb_cfg_data usb_config = {.interface_descriptor = &usb_interface};
struct device {
    const void *config;
};
struct zmk_behavior_binding {
    const char *behavior_dev;
    uint32_t param1, param2;
};
struct zmk_behavior_binding_event {
    uint32_t position;
    uint8_t source;
    int64_t timestamp;
};
struct zmk_position_state_changed {
    uint8_t source;
    uint32_t position;
    bool state;
    int64_t timestamp;
};
typedef struct zmk_position_state_changed zmk_event_t;
static const struct zmk_position_state_changed *
as_zmk_position_state_changed(const zmk_event_t *e) {
    return e;
}
struct behavior_driver_api {
    int (*binding_pressed)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
    int (*binding_released)(struct zmk_behavior_binding *, struct zmk_behavior_binding_event);
    int locality;
};
static struct device control_device, usb_device;
static const struct device *zmk_behavior_get_binding(const char *name) {
    assert(!strcmp(name, "klor_ctrl"));
    return &control_device;
}
static const struct device *device_get_binding(const char *name) {
    assert(!strcmp(name, "HID_1"));
    return &usb_device;
}
static struct zmk_behavior_binding layers[5][44];
static bool active_layers[5];
static bool zmk_keymap_layer_active(unsigned layer) { return active_layers[layer]; }
static unsigned zmk_keymap_highest_layer_active(void) {
    for (int i = 4; i >= 0; i--)
        if (active_layers[i])
            return i;
    return 0;
}
static const struct zmk_behavior_binding *zmk_keymap_get_layer_binding_at_idx(unsigned l,
                                                                              unsigned p) {
    return &layers[l][p];
}
static int zmk_keymap_layer_activate(unsigned layer, bool ignored) {
    (void)ignored;
    active_layers[layer] = true;
    return 0;
}
static int zmk_keymap_layer_deactivate(unsigned layer, bool ignored) {
    (void)ignored;
    active_layers[layer] = false;
    return 0;
}
static uint8_t explicit_mods;
static uint8_t zmk_hid_get_explicit_mods(void) { return explicit_mods; }
static struct {
    uint32_t key;
    bool down;
} keys[256];
static unsigned key_count;
static int raise_zmk_keycode_state_changed_from_encoded(uint32_t key, bool state, int64_t time) {
    (void)time;
    assert(key_count < 256);
    keys[key_count].key = key;
    keys[key_count++].down = state;
    return 0;
}

static int64_t now;
struct k_work {
    void (*handler)(struct k_work *);
};
struct k_work_delayable {
    struct k_work work;
    int64_t due;
    bool pending;
};
#define K_WORK_DEFINE(name, fn) struct k_work name = {.handler = fn}
#define K_WORK_DELAYABLE_DEFINE(name, fn) struct k_work_delayable name = {.work = {.handler = fn}}
static int k_work_submit(struct k_work *work) {
    work->handler(work);
    return 0;
}
static int k_work_cancel_delayable(struct k_work_delayable *work) {
    work->pending = false;
    return 0;
}
static int k_work_reschedule(struct k_work_delayable *work, int delay) {
    work->due = now + delay;
    work->pending = true;
    return 0;
}
struct semaphore {
    unsigned count;
};
#define K_SEM_DEFINE(name, initial, limit) struct semaphore name = {.count = initial}
static int k_sem_take(struct semaphore *sem, int timeout) {
    (void)timeout;
    if (!sem->count)
        return -EAGAIN;
    sem->count--;
    return 0;
}
static void k_sem_give(struct semaphore *sem) { sem->count = 1; }
struct msgq {
    uint8_t data[16][32];
    unsigned head, count;
};
#define K_MSGQ_DEFINE(name, size, n, alignment) struct msgq name
static int k_msgq_put(struct msgq *queue, const void *data, int timeout) {
    (void)timeout;
    if (queue->count == 16)
        return -ENOSPC;
    memcpy(queue->data[(queue->head + queue->count) % 16], data, 32);
    queue->count++;
    return 0;
}
static void k_msgq_purge(struct msgq *queue) { queue->head = queue->count = 0; }
static int k_msgq_get(struct msgq *queue, void *data, int timeout) {
    (void)timeout;
    if (!queue->count)
        return -EAGAIN;
    memcpy(data, queue->data[queue->head], 32);
    queue->head = (queue->head + 1) % 16;
    queue->count--;
    return 0;
}
struct hid_ops {
    void (*int_in_ready)(const struct device *);
    void (*int_out_ready)(const struct device *);
};
static uint8_t packets[256][32], incoming[32];
static unsigned packet_count;
static uint32_t incoming_length = 32;
static const uint8_t *descriptor;
static size_t descriptor_size;
static int hid_int_ep_write(const struct device *dev, const void *data, size_t len,
                            uint32_t *written) {
    (void)dev;
    assert(len == 32 && packet_count < 256);
    memcpy(packets[packet_count++], data, len);
    *written = len;
    return 0;
}
static int hid_int_ep_read(const struct device *dev, void *data, size_t capacity,
                           uint32_t *length) {
    (void)dev;
    assert(capacity >= incoming_length);
    memcpy(data, incoming, incoming_length);
    *length = incoming_length;
    return 0;
}
static void usb_hid_register_device(const struct device *dev, const uint8_t *desc, size_t size,
                                    const struct hid_ops *ops) {
    (void)dev;
    (void)ops;
    descriptor = desc;
    descriptor_size = size;
}
static int usb_hid_init(const struct device *dev) {
    (void)dev;
    return 0;
}
