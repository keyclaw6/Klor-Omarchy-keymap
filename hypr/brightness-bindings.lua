-- KLOR external monitor brightness: standard media keys from existing firmware.
-- Quattro's default bindings change only the focused monitor and drop busy
-- events. Our helper queues every turn and changes both DDC monitors.
local helper = os.getenv("HOME") .. "/.config/hypr/brightness-display-ddc.sh"
for _, binding in ipairs({
  { "XF86MonBrightnessUp", "Both monitors brightness up", "up 5" },
  { "XF86MonBrightnessDown", "Both monitors brightness down", "down 5" },
  { "ALT + XF86MonBrightnessUp", "Both monitors brightness up precise", "up 1" },
  { "ALT + XF86MonBrightnessDown", "Both monitors brightness down precise", "down 1" },
}) do
  hl.unbind(binding[1])
  o.bind(binding[1], binding[2], '"' .. helper .. '" ' .. binding[3], { locked = true, repeating = true })
end
