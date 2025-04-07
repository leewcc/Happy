cmake_minimum_required(VERSION 3.10)
project(THS_Monitor)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找依赖包
find_package(Detours CONFIG REQUIRED)

# 添加头文件路径
include_directories(${CMAKE_SOURCE_DIR}/include)

# 添加 DLL 项目
add_library(duanxianjingling SHARED 
    duanxianjingling.cpp
)

# 链接依赖库
target_link_libraries(duanxianjingling PRIVATE
    detours
    ws2_32
    wininet
)

# 添加注入器项目
add_executable(injector
    injector.cpp
) 