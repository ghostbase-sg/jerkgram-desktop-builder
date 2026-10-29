# Supported initial-cache loading; never modifies the production cache or prints values.
if(NOT DEFINED ENV{JERKGRAM_PRODUCTION_OUT})
    message(FATAL_ERROR "Existing production cache path is required")
endif()
load_cache("$ENV{JERKGRAM_PRODUCTION_OUT}" READ_WITH_PREFIX _previous_
    TDESKTOP_API_ID TDESKTOP_API_HASH TDESKTOP_API_TEST)
if(NOT _previous_TDESKTOP_API_ID MATCHES "^[1-9][0-9]*$"
    OR NOT _previous_TDESKTOP_API_HASH MATCHES "^[0-9a-fA-F]+$"
    OR _previous_TDESKTOP_API_TEST)
    message(FATAL_ERROR "Existing configured client credentials are unavailable/invalid")
endif()
string(LENGTH "${_previous_TDESKTOP_API_HASH}" _hash_length)
if(NOT _hash_length EQUAL 32)
    message(FATAL_ERROR "Existing client configuration is invalid")
endif()
set(TDESKTOP_API_ID "${_previous_TDESKTOP_API_ID}" CACHE STRING "Configured client API")
set(TDESKTOP_API_HASH "${_previous_TDESKTOP_API_HASH}" CACHE STRING "Configured client API")
set(TDESKTOP_API_TEST OFF CACHE BOOL "Use configured client API")
