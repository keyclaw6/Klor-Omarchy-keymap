if(CONFIG_KLOR_OMARCHY)
  target_include_directories(app PRIVATE include)
  target_sources(app PRIVATE src/klor_omarchy.c)
endif()
