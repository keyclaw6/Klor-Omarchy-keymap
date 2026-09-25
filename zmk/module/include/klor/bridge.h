#pragma once

#include <stdint.h>

int klor_bridge_send_packet(const uint8_t packet[32]);
int klor_bridge_send_action(uint8_t action_id, uint8_t param);
