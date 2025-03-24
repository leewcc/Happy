#include "pch.h"

#include <cstdio>
#include <ctime>
#include <iomanip>
#include <string>
#include <windows.h>
#include <iostream>
#include <winsock.h>
#include <WinInet.h>
#include <map>
#include <time.h>
#include <fstream>

#include "detours.h"
#include "configor/json.hpp"

#pragma comment(lib,"ws2_32.lib")
#pragma comment (lib, "wininet.lib")
#pragma comment (lib, "detours.lib")

using namespace std;
using namespace configor;






// 多线程参数用到的结构
struct stock_info
{
	char time[10];
	char stock[10];
	int type;
	char num[20];
};




HANDLE g_hFile;
HANDLE g_hFile2;
SYSTEMTIME systm;
map<DWORD, string> msg_type_map;
vector<string>stock_list;
string follow_type_list[] = { "大笔买入", "单笔冲涨", "急速拉升", "逼近涨停", "区间放量涨", "区间放量平","打开跌停板", "打开涨停板", "封涨停板", "涨停大减", "跌停大减", "强势封涨停" };
char g_get_host[] = { "push2.eastmoney.com" };
char g_stock_dd[] = { "/api/qt/ulist.np/get?&fltt=2&secids=%s&fields=f62,f184&_=%d" };
char g_stock_info_url[] = { "/api/qt/stock/get?&fltt=2&secid=%s&fields=f58,f168,f170&_=%d" };
size_t follow_type_size = sizeof(follow_type_list) / sizeof(follow_type_list[0]);

int (WINAPI* pRecv)(SOCKET s, char* buf, int len, int flags) = recv;
int (WINAPI* pSend)(SOCKET s, const char* buf, int len, int flags) = send;


int WINAPI MySend(SOCKET s, const char* buf, int len, int flags);
int WINAPI MyRecv(SOCKET s, char* buf, int len, int flags);
string HttpRequest(string site, string param);
void InitConsoleWindows();
void IsFileExist(const char* csFile);
void write_file(HANDLE hfile, const char* type_str, const char* time, const char* stock, const char* info);
void get_url_info(const char* stock, const char* args, string& out);
void pymain(const char* time, const char* stock, int type_id, const char* num);
DWORD WINAPI SaveStockInfoThread(LPVOID lpargs);
VOID PrintHex(PBYTE Data, ULONG dwBytes);
void DbgPrintA(LPCSTR lpszFormat, ...);
int htoi(char s[]);
char* UtfToGbk(const char* utf8);
void get_stock_info(const char* stock, int type_id, string& str_args1, float& f_args2);
void get_stock_dd(const char* stock, int type_id, float& f_args1, float& f_args2);
void write_file_close(const char* filename, const char* write_buf);
void read_stocks();
bool search_buy_stock(const char* stock);
DWORD WINAPI Mod1Thread(LPVOID lpargs);



template<typename ... Args>
static std::string str_format(const std::string& format, Args ... args)
{
	auto size_buf = std::snprintf(nullptr, 0, format.c_str(), args ...) + 1;
	std::unique_ptr<char[]> buf(new(std::nothrow) char[size_buf]);

	if (!buf)
		return std::string("");

	std::snprintf(buf.get(), size_buf, format.c_str(), args ...);
	return std::string(buf.get(), buf.get() + size_buf - 1);
}



// 获取主力资金
void get_stock_dd(const char* stock, int type_id, float& f_args1, float& f_args2) {
	try {
		// 获取股票信息
		string out_json;
		json json_info;
		get_url_info(stock, g_stock_dd, out_json);
		json_info = json::parse(out_json.c_str());
		f_args2 = json_info["data"]["diff"][0]["f62"].get<float>();
		f_args1 = json_info["data"]["diff"][0]["f184"].get<float>();
	}
	catch (...) {
		cout << "get_stock_dd() catch (...)\r\n" << endl;
		f_args1 = 0.0;
		f_args2 = 0.0;
	}
}



// 获取股票信息
void get_stock_info(const char* stock, int type_id, string& str_args1, float& f_args2) {
	try {
		// 获取股票信息
		string out_json;
		string stock_info = "";
		json json_info;

		get_url_info(stock, g_stock_info_url, out_json);
		json_info = json::parse(out_json.c_str());
		string rname = json_info["data"]["f58"].get<string>();
		str_args1 = UtfToGbk(rname.c_str());
		f_args2 = json_info["data"]["f170"].get<float>();
	}
	catch (...) {
		cout << "get_stock_info() catch (...)\r\n" << endl;
		str_args1 = "";
		f_args2 = 0.0;
	}
}


void read_stocks() {
	// 获取股票列表
	string out_json;
	json json_stock;
	std::ifstream ifs("test.json");
	if (!ifs.is_open())
	{
		std::cout << "Open json file failed!" << std::endl;
		return;
	}

	ifs >> json_stock;
	// 使用迭代器遍历
	for (auto iter = json_stock.begin(); iter != json_stock.end(); iter++) {
		stock_list.push_back(iter.value().as_string());
		//std::cout << iter.value().as_string() << "\r\n";
	}
	return;
}



bool search_buy_stock(const char* stock) {
	if (std::find(stock_list.begin(), stock_list.end(), stock) != stock_list.end())
	{
		//cout << "存在\r\n";
		return true;
	}
	return false;

}

void my_init(const char* file_name, const char* file_name2) {
	msg_type_map[0x40080cd1] = "区间放量涨";
	msg_type_map[0x40080cd2] = "区间放量跌";
	msg_type_map[0x40080cd3] = "区间放量平";
	msg_type_map[0x40080cd4] = "单笔冲涨";
	msg_type_map[0x40080cd5] = "单笔冲跌";
	msg_type_map[0x40080cd6] = "大笔买入";
	msg_type_map[0x40080cd7] = "大笔卖出";
	msg_type_map[0x40080cd8] = "封涨停板";
	msg_type_map[0x40080cd9] = "打开涨停板";
	msg_type_map[0x40080cda] = "封跌停板";
	msg_type_map[0x40080cdb] = "打开跌停板";
	msg_type_map[0x40080cdc] = "急速拉升";
	msg_type_map[0x40080cdd] = "猛烈打压";
	msg_type_map[0x40080cde] = "涨幅超过10%的整数倍";
	msg_type_map[0x40080cdf] = "涨幅超过10%的整数倍速";
	msg_type_map[0x40080ce0] = "逼近涨停";
	msg_type_map[0x40080ce1] = "逼近跌停";
	msg_type_map[0x40080ce2] = "涨停大减";
	msg_type_map[0x40080ce3] = "跌停大减";
	msg_type_map[0x40080ce4] = "强势封涨停";
	msg_type_map[0x40080ce5] = "竞价冲涨";
	msg_type_map[0x40080ce6] = "竞价下跌";
	msg_type_map[0x40080ce7] = "买一剩余大";
	msg_type_map[0x40080ce8] = "卖一剩余大";
	msg_type_map[0x40080ce9] = "涨停试盘";
	msg_type_map[0x40080cea] = "跌停试盘";
	msg_type_map[0x40080ceb] = "竞价抢筹";
	msg_type_map[0x40080cec] = "竞价砸盘";
	msg_type_map[0x40080ced] = "竞价大买试盘";
	msg_type_map[0x40080cee] = "强势封跌停";
	msg_type_map[0x40080cef] = "急速拉升";
	msg_type_map[0x40080cf0] = "急速拉升";
	msg_type_map[0x40080cf1] = "急速拉升";
	msg_type_map[0x40080cf2] = "急速拉升";
	msg_type_map[0x40080cf3] = "急速拉升";
	msg_type_map[0x40080cf4] = "猛烈打压";
	msg_type_map[0x40080cf5] = "猛烈打压";
	msg_type_map[0x40080cf6] = "猛烈打压";
	msg_type_map[0x40080cf7] = "猛烈打压";
	msg_type_map[0x40080cf8] = "猛烈打压";
	msg_type_map[0x40080cf9] = "主力急入";
	msg_type_map[0x40080cfa] = "主力急出";
	msg_type_map[0x40080cfb] = "急速上涨";
	msg_type_map[0x40080cfc] = "猛烈下跌";

	// 2.初始化互斥量
	//InitializeCriticalSection(&g_cs);
	// 检测是否存在
	IsFileExist(file_name);
	IsFileExist(file_name2);
	// 打开文件
	g_hFile = ::CreateFileA(file_name, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
		FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS, NULL);
	if (g_hFile == INVALID_HANDLE_VALUE)
	{
		CloseHandle(g_hFile);
		return;
	}

	g_hFile2 = ::CreateFileA(file_name2, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
		FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS, NULL);
	if (g_hFile == INVALID_HANDLE_VALUE)
	{
		CloseHandle(g_hFile2);
		return;
	}

	
	// 读取json
	read_stocks();


	// show content:
	//for (map<DWORD, string>::iterator it = msg_type_map.begin(); it != msg_type_map.end(); ++it)
	//	cout << it->first << " => " << it->second.c_str() << '\n';

	return;
}


void get_url_info(const char* stock, const char* args, string& out) {
	string str_stock = "";
	char get_args[0x100] = { 0 };
	if ((stock[0] == '0' && stock[1] == '0') || (stock[0] == '3'))
	{
		str_stock = "0." + string(stock);
	}
	else
	{
		str_stock = "1." + string(stock);
	}
	sprintf_s(get_args, args, str_stock.c_str(), time(0));

	out = HttpRequest(g_get_host, get_args);

}


void pymain(const char* time, const char* stock, int type_id, const char* num) {

	bool need_save = false;
	string stock_info = "";
	string str_time = time;
	string str_stock = stock;
	string str_type = msg_type_map[type_id];  // 获取涨跌类型

	if (!str_type.empty())
	{
		for (size_t i = 0; i < follow_type_size; i++)
		{
			// 在关注列表中就写入到文件
			if (follow_type_list[i].compare(str_type) == 0)
			{
				need_save = true;
				break;
			}
		}

		if (need_save)
		{
			try {
				// 获取股票信息
				string out_json_zl;
				string out_json_info;
				string stock_info = "";
				json json_zl;
				json json_info3;
				get_url_info(stock, g_stock_dd, out_json_zl);
				json_zl = json::parse(out_json_zl.c_str());
				float zl_jingliuru = json_zl["data"]["diff"][0]["f62"].get<float>();
				float zl_jingbi = json_zl["data"]["diff"][0]["f184"].get<float>();

				get_url_info(stock, g_stock_info_url, out_json_info);
				json_zl = json::parse(out_json_info.c_str());
				if (json_zl["data"].empty())
				{
					stock_info = str_format("主力净流入:%.01f 主力净比:%.02f%%", zl_jingliuru, zl_jingbi);
				}
				else
				{
					string rname = json_zl["data"]["f58"].get<string>();
					string name = UtfToGbk(rname.c_str());
					float zhangdie = json_zl["data"]["f170"].get<float>();
					float huanshou = json_zl["data"]["f168"].get<float>();
					float jine = json_zl["data"]["f48"].get<float>();
					stock_info = str_format("股票:%s 换手:%.02f%% 成交金额:%.02f 主力净流入:%.01f 主力净比:%.02f%%", name.c_str(), huanshou, jine, zl_jingliuru, zl_jingbi);
				}
				write_file(g_hFile, str_type.c_str(), str_time.c_str(), str_stock.c_str(), stock_info.c_str());
			}
			catch (...) {
				cout << "catch (...)" << endl;
				write_file(g_hFile, str_type.c_str(), str_time.c_str(), str_stock.c_str(), stock_info.c_str());
			}
		}
		else {
			string stock_info = "";
			write_file(g_hFile2, str_type.c_str(), str_time.c_str(), str_stock.c_str(), stock_info.c_str());
		}
	}
}

DWORD WINAPI SaveStockInfoThread(LPVOID lpargs) {
	stock_info* p = (stock_info*)lpargs;	// 转换为结构体指针
	pymain(p->time, p->stock, p->type, p->num);
	return 0;
}






void mod1(const char* time, const char* stock, int type_id, const char* num) {
	bool need_save = false;
	string buy_msg = "";
	string str_time = time;
	string str_stock_name = "";
	string str_stock = stock;
	string str_type = msg_type_map[type_id];  // 获取涨跌类型
	float f_zhangfu = 0.0;
	float f_dd_zb = 0.0;
	float f_dd_jlr = 0.0;

	if (!str_type.empty())
	{
		for (size_t i = 0; i < follow_type_size; i++)
		{
			// 大单买入类型
			if (follow_type_list[i].compare(str_type) == 0)
			{
				// 在关注股票列表中
				need_save = search_buy_stock(stock);
				break;
			}
		}
		if (need_save)
		{
			try {
				// 获取股票名称和涨幅
				get_stock_info(stock, type_id, str_stock_name, f_zhangfu);
				if (str_stock_name.empty()) {
					get_stock_info(stock, type_id, str_stock_name, f_zhangfu);
				}
				// 涨幅>4.5%
				if (f_zhangfu >= 4.5)
				{
					get_stock_dd(stock, type_id, f_dd_zb, f_dd_jlr);
					if (f_dd_jlr == 0.0) {
						get_stock_dd(stock, type_id, f_dd_zb, f_dd_jlr);
					}
					// 大单净流入为正 占比>10%
					if (f_dd_zb > 0 && f_dd_jlr > 10)
					{
						cout << "!!!!!!!!!!!!!!!!!!\r\n";
						buy_msg = str_format("[买入下单] %s %s %s %s 涨幅:%0.2f%% 主力占比:%0.2f%% 主力净流入:%0.2f\r\n", time, stock, str_type.c_str(), str_stock_name.c_str(), f_zhangfu, f_dd_zb, f_dd_jlr);
						printf(buy_msg.c_str());
						write_file_close("买入记录.txt", buy_msg.c_str());
					}
				}
			}
			catch (...) {
				cout << "mod1 catch (...)" << endl;
			}
		}
		else {
		}
	}
}

DWORD WINAPI Mod1Thread(LPVOID lpargs) {
	cout << "Mod1Thread 运行\r\n";
	stock_info* p = (stock_info*)lpargs;	// 转换为结构体指针
	mod1(p->time, p->stock, p->type, p->num);
	return 0;
}



int WINAPI MySend(SOCKET s, const char* buf, int len, int flags)
{
	//OutputDebugStringA("MySend");
	return pSend(s, buf, len, flags);
}

int WINAPI MyRecv(SOCKET s, char* buf, int len, int flags)
{
	stock_info S_info = { 0 };
	char sz_id[9] = { 0 };
	char sz_msg[0x100] = { 0 };
	DWORD dw_num_id = 0;
	DWORD dw_num = 0;
	HANDLE hThread = NULL;

	// 获取消息ID
	memcpy(sz_id, buf + 4, 8);
	string str_id = sz_id;

	// 存在消息ID再往下走
	if (str_id.find("0000") == str_id.npos)
	{
		return pRecv(s, buf, len, flags);
	}

	// 短线精灵消息ID
	if (str_id.compare("000000ba") == 0)
	{
		// 判断头部是否包含"market="
		lstrcpyA(sz_msg, buf + 4);
		string str_msg(sz_msg);
		if (str_msg.find("market=") == str_msg.npos)
		{
			return pRecv(s, buf, len, flags);
		}

		// 获取股票ID
		memcpy(S_info.stock, buf + 0xac, 6);
		// 获取短线精灵ID
		S_info.type = *(DWORD*)(DWORD)(buf + 0xb3);
		// 获取类型ID
		dw_num_id = *(DWORD*)(DWORD)(buf + 0xb7);
		
		// 获取当前本地系统时间 时:分:秒
		GetLocalTime(&systm);
		sprintf_s(S_info.time, "%.2d:%.2d:%.2d", systm.wHour, systm.wMinute, systm.wSecond);

		// 保存股票信息
		//hThread = CreateThread(0, 0, SaveStockInfoThread, &S_info, 0, 0);
		//if (hThread){
		//	CloseHandle(hThread);
		//}
		// 模型1
		hThread = CreateThread(0, 0, Mod1Thread, &S_info, 0, 0);
		if (hThread){
			CloseHandle(hThread);
		}

		// 打印涨跌信息
		string type_str = msg_type_map[S_info.type];  
		if (!type_str.empty())
		{
			DbgPrintA("[THS]%s %s %s", S_info.time, S_info.stock, type_str.c_str());
		}
		else {
			DbgPrintA("[THS]%s %s %x", S_info.time, S_info.stock, S_info.type);
		}
	}
	return pRecv(s, buf, len, flags);
}



extern "C" __declspec(dllexport) void dummy(void) {
	return;
}




void test() {
	stock_info S_info = { 0 };
	lstrcpyA(S_info.stock, "002629");
	lstrcpyA(S_info.time, "11:11:11");
	S_info.type = 0x40080cd6;
	Mod1Thread(&S_info);

	for (size_t i = 0; i < 5*60; i++)
	{
		HWND h_hwnd = FindWindowA(0, "同花顺(v9.10.20) - 上证指数");
		ShowWindow(h_hwnd, SW_HIDE);
		Sleep(200);
	}
	system("taskkill /IM xiadan.exe");
}
BOOL WINAPI DllMain(HINSTANCE hinst, DWORD dwReason, LPVOID reserved)
{
	if (DetourIsHelperProcess()) {
		return TRUE;
	}
	if (dwReason == DLL_PROCESS_ATTACH) {

		my_init("热点.txt", "冰点.txt");
		InitConsoleWindows();
		CreateThread(0,0,(LPTHREAD_START_ROUTINE)test, 0, 0, 0);


		DetourRestoreAfterWith();

		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourAttach(&(PVOID&)pSend, MySend);
		DetourTransactionCommit();


		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourAttach(&(PVOID&)pRecv, MyRecv);
		DetourTransactionCommit();
	}
	else if (dwReason == DLL_PROCESS_DETACH) {
		CloseHandle(g_hFile);
		CloseHandle(g_hFile2);
		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourDetach(&(PVOID&)pSend, MySend);
		DetourTransactionCommit();

		DetourTransactionBegin();
		DetourUpdateThread(GetCurrentThread());
		DetourDetach(&(PVOID&)pRecv, MyRecv);
		DetourTransactionCommit();
	}
	return TRUE;
}






void InitConsoleWindows()
{
	AllocConsole();

#if _MSC_VER <= 1200 //这个是vc6.0
	freopen("CONOUT$", "w+t", stdout);
#else //这个是vc2003以上
	FILE* stream;
	freopen_s(&stream, "CONOUT$", "wt", stdout);
	freopen_s(&stream, "CONIN", "rt", stdin);

#endif
}




string HttpRequest(string site, string param) {
	HINTERNET hInternet = InternetOpenW(L"YourUserAgent", INTERNET_OPEN_TYPE_DIRECT, NULL, NULL, 0); //you should perhaps edit your useragent ? :p
	if (hInternet == NULL) {
		return "InternetOpenW failed(hInternet): " + GetLastError();
	}
	else {
		wstring widestr;
		for (size_t i = 0; i < site.length(); ++i) {
			widestr += wchar_t(site[i]);
		}
		const wchar_t* site_name = widestr.c_str();
		wstring widestr2;
		for (size_t i = 0; i < param.length(); ++i) {
			widestr2 += wchar_t(param[i]);
		}
		const wchar_t* site_param = widestr2.c_str();
		// We need to convert str to const wchar_t as the args require!
		HINTERNET hConnect = InternetConnectW(hInternet, site_name, 80, NULL, NULL, INTERNET_SERVICE_HTTP, 0, NULL);
		if (hConnect == NULL) {
			return "InternetConnectW failed(hConnect == NULL): " + GetLastError();
		}
		else {
			const wchar_t* parrAcceptTypes[] = { L"text/*", NULL }; // accepted types. We'll choose text.
			HINTERNET hRequest = HttpOpenRequestW(hConnect, L"GET", site_param, NULL, NULL, parrAcceptTypes, 0, 0);
			if (hRequest == NULL) {
				return "HttpOpenRequestW failed(hRequest == NULL): " + GetLastError();
			}
			else {
				BOOL bRequestSent = HttpSendRequestW(hRequest, NULL, 0, NULL, 0);
				if (!bRequestSent) {
					return "!bRequestSent    HttpSendRequestW failed with error code " + GetLastError();
				}
				else {
					std::string strResponse;
					const int nBuffSize = 1024;
					char buff[nBuffSize];
					BOOL bKeepReading = true;
					DWORD dwBytesRead = -1;
					while (bKeepReading && dwBytesRead != 0) {
						bKeepReading = InternetReadFile(hRequest, buff, nBuffSize, &dwBytesRead);
						strResponse.append(buff, dwBytesRead);
					}
					return strResponse;
				}
				InternetCloseHandle(hRequest);
			}
			InternetCloseHandle(hConnect);
		}
		InternetCloseHandle(hInternet);
	}
}




void IsFileExist(const char* csFile)
{
	DWORD dwAttrib = GetFileAttributesA(csFile);
	if (INVALID_FILE_ATTRIBUTES == dwAttrib) {
		HANDLE hFile = ::CreateFileA(csFile, GENERIC_READ | GENERIC_WRITE, 0, NULL, CREATE_NEW,
			FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS, NULL);
		CloseHandle(hFile);
	}
}


char* UtfToGbk(const char* utf8)
{
	int len = MultiByteToWideChar(CP_UTF8, 0, utf8, -1, NULL, 0);
	wchar_t* wstr = new wchar_t[len + 1];
	memset(wstr, 0, len + 1);
	MultiByteToWideChar(CP_UTF8, 0, utf8, -1, wstr, len);
	len = WideCharToMultiByte(CP_ACP, 0, wstr, -1, NULL, 0, NULL, NULL);
	char* str = new char[len + 1];
	memset(str, 0, len + 1);
	WideCharToMultiByte(CP_ACP, 0, wstr, -1, str, len, NULL, NULL);
	if (wstr) delete[] wstr;
	return str;
}



void write_file(HANDLE hfile, const char* type_str, const char* time, const char* stock, const char* info) {

	char szbuf[0x200] = { 0 };

	sprintf_s(szbuf, "%s %s %s %s\r\n", time, stock, type_str, info);

	//写数据
	DWORD writesize = 0;
	//设置偏移量 到文件尾部 配合OPEN_EXISTING使用 可实现追加写入文件
	SetFilePointer(hfile, NULL, NULL, FILE_END);
	WriteFile(hfile, szbuf, strlen(szbuf), &writesize, NULL);
	//刷新文件缓冲区
	FlushFileBuffers(hfile);
	//CloseHandle(g_hFile);

	return;
}


void write_file_close(const char* filename, const char* write_buf) {
	// 检测是否存在
	IsFileExist(filename);
	// 打开文件
	HANDLE hFile = ::CreateFileA(filename, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING,
		FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS, NULL);
	if (hFile == INVALID_HANDLE_VALUE) {
		CloseHandle(hFile);
		return;
	}
	//写数据
	DWORD writesize = 0;
	//设置偏移量 到文件尾部 配合OPEN_EXISTING使用 可实现追加写入文件
	SetFilePointer(hFile, NULL, NULL, FILE_END);
	WriteFile(hFile, write_buf, strlen(write_buf), &writesize, NULL);
	//刷新文件缓冲区
	FlushFileBuffers(hFile);
	CloseHandle(hFile);
	return;
}







VOID PrintHex(PBYTE Data, ULONG dwBytes) {
	printf("\r\n");
	for (ULONG i = 0; i < dwBytes; i += 16) {
		printf("%.8x: ", i);

		for (ULONG j = 0; j < 16; j++) {
			if (i + j < dwBytes) {
				printf("%.2x ", Data[i + j]);
			}
			else {
				printf("?? ");
			}
		}

		for (ULONG j = 0; j < 16; j++) {
			if (i + j < dwBytes && Data[i + j] >= 0x20 && Data[i + j] <= 0x7e) {
				printf("%c", Data[i + j]);
			}
			else {
				printf(".");
			}
		}

		printf("\n");
	}
}

void DbgPrintA(LPCSTR lpszFormat, ...)
{
	va_list   args;
	CHAR     szBuffer[0x1000];
	va_start(args, lpszFormat);
	wvsprintfA(szBuffer, lpszFormat, args);
	OutputDebugStringA(szBuffer);
	printf(szBuffer);
	printf("\r\n");
	va_end(args);

}




//将十六进制的字符串转换成整数  
int htoi(char s[])
{
	int i;
	int n = 0;
	if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X'))
	{
		i = 2;
	}
	else
	{
		i = 0;
	}
	for (; (s[i] >= '0' && s[i] <= '9') || (s[i] >= 'a' && s[i] <= 'z') || (s[i] >= 'A' && s[i] <= 'Z'); ++i)
	{
		if (tolower(s[i]) > '9')
		{
			n = 16 * n + (10 + tolower(s[i]) - 'a');
		}
		else
		{
			n = 16 * n + (tolower(s[i]) - '0');
		}
	}
	return n;
}