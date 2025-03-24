cmake_minimum_required(VERSION 3.10)
project(stock_monitor)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 添加库目录
link_directories(${CMAKE_SOURCE_DIR}/lib)

# 创建 DLL
add_library(duanxianjingling SHARED
    duanxianjingling.cpp
)

# 添加包含目录
target_include_directories(duanxianjingling PRIVATE
    ${CMAKE_SOURCE_DIR}/lib
)

# 链接需要的库
target_link_libraries(duanxianjingling
    ws2_32
    wininet
    detours
)

# 创建测试程序
add_executable(test
    test.cpp
)

# 链接 DLL
target_link_libraries(test
    duanxianjingling
) 