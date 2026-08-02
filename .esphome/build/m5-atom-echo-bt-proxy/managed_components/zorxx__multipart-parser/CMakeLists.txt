# Copyright 2023 Zorxx Software. All rights reserved.

# esp-idf component
if(IDF_TARGET)
   idf_component_register(SRCS "multipart_parser.c" INCLUDE_DIRS ".")
   return()
endif()

cmake_minimum_required(VERSION 3.0)
set(project multipart_parser)
project(${project} LANGUAGES C VERSION 1.0.1)

add_library(${project} SHARED multipart_parser.c)
set_target_properties(${project} PROPERTIES PUBLIC_HEADER "multipart_parser.h")
target_include_directories(${project} INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})
install(TARGETS ${project}
        LIBRARY DESTINATION lib
        PUBLIC_HEADER DESTINATION include/multipart_parser)

#target_compile_definitions(${project} PRIVATE -DDEBUG_MULTIPART)

add_subdirectory(test)
