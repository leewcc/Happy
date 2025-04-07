#include <windows.h>

int main() {
    // 目标进程名
    LPCSTR processName = "xiadan.exe";  // 同花顺下单程序
    
    // DLL 路径
    LPCSTR dllPath = "duanxianjingling.dll";
    
    // 获取进程句柄
    DWORD processId = 0;
    HWND hwnd = FindWindowA(NULL, "同花顺(v9.10.20) - 上证指数");
    GetWindowThreadProcessId(hwnd, &processId);
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, processId);
    
    // 在目标进程中分配内存
    LPVOID dllPathAddr = VirtualAllocEx(hProcess, NULL, strlen(dllPath) + 1, 
                                      MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    
    // 写入 DLL 路径
    WriteProcessMemory(hProcess, dllPathAddr, dllPath, strlen(dllPath) + 1, NULL);
    
    // 获取 LoadLibraryA 地址
    HMODULE hKernel32 = GetModuleHandleA("Kernel32");
    LPVOID loadLibraryAddr = GetProcAddress(hKernel32, "LoadLibraryA");
    
    // 创建远程线程加载 DLL
    CreateRemoteThread(hProcess, NULL, 0, 
                      (LPTHREAD_START_ROUTINE)loadLibraryAddr,
                      dllPathAddr, 0, NULL);
    
    return 0;
} 