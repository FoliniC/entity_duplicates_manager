# Copyright 2023 Zorxx Software. All rights reserved.
add_executable(test main.c)
target_link_libraries(test multipart_parser)
target_include_directories(test PRIVATE ..)
