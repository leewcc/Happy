#include <windows.h>
#include <iostream>

// 引入 DLL 中的函数声明
extern "C" void dummy(void);

int main() {
    // 加载 DLL
    HMODULE hDll = LoadLibrary("duanxianjingling.dll");
    if (hDll == NULL) {
        std::cout << "Failed to load DLL" << std::endl;
        return 1;
    }

    // 调用 DLL 中的函数
    dummy();

    // 等待一段时间观察结果
    Sleep(10000);

    // 卸载 DLL
    FreeLibrary(hDll);
    return 0;
} 