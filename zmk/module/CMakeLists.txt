if(CONFIG_KLOR_OMARCHY)
  target_include_directories(app PRIVATE include)
  # Observers must precede ZMK's capturing hold-tap and keymap listeners.
  target_sources(app PRIVATE src/klor_boot.c)
  if((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    target_sources(app PRIVATE src/klor_omarchy.c src/behavior_klor_unicode.c)
  endif()
endif()
