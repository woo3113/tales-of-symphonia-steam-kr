// 32-bit logging DLL, drop-in as korfnt\korfnt.dll
// Hooks the char-converter (exe+0x17A81C) and glyph-UV func (exe+0x178680)
#include <windows.h>

#define RING 1024
#define MASK (RING-1)
#define OFF_CONV 0x17A81C
#define OFF_GLYPH 0x178680

typedef struct { unsigned int a, b; } ENT;

static unsigned char* g_mem;
static unsigned int* g_idx0;
static unsigned int* g_idx1;
static ENT* g_buf0;
static ENT* g_buf1;
static char g_out[MAX_PATH] = {0};

static void wr32(unsigned char* p, unsigned int v){ p[0]=(unsigned char)v; p[1]=(unsigned char)(v>>8); p[2]=(unsigned char)(v>>16); p[3]=(unsigned char)(v>>24); }

static int build_conv(unsigned char* s, unsigned int idx, unsigned int buf, unsigned int resume){
    unsigned char* p=s;
    *p++=0x52;
    *p++=0x8B; *p++=0x15; wr32(p,idx); p+=4;
    *p++=0x89; *p++=0x04; *p++=0xD5; wr32(p,buf); p+=4;
    *p++=0x8B; *p++=0x4C; *p++=0x24; *p++=0x04;
    *p++=0x89; *p++=0x0C; *p++=0xD5; wr32(p,buf+4); p+=4;
    *p++=0x83; *p++=0xC2; *p++=0x01;
    *p++=0x81; *p++=0xE2; wr32(p,MASK); p+=4;
    *p++=0x89; *p++=0x15; wr32(p,idx); p+=4;
    *p++=0x5A;
    *p++=0xB9; wr32(p,0x80); p+=4;
    *p++=0xE9; { unsigned int next=(unsigned int)(p+4); wr32(p,(unsigned int)(resume-next)); p+=4; }
    return (int)(p-s);
}
static int build_glyph(unsigned char* s, unsigned int idx, unsigned int buf, unsigned int resume){
    unsigned char* p=s;
    *p++=0x52;
    *p++=0x8B; *p++=0x15; wr32(p,idx); p+=4;
    *p++=0x89; *p++=0x04; *p++=0xD5; wr32(p,buf); p+=4;      // [edx*8+buf]=eax (code)
    *p++=0x89; *p++=0x0C; *p++=0xD5; wr32(p,buf+4); p+=4;    // [edx*8+buf+4]=ecx (font ctx)
    *p++=0x83; *p++=0xC2; *p++=0x01;
    *p++=0x81; *p++=0xE2; wr32(p,MASK); p+=4;
    *p++=0x89; *p++=0x15; wr32(p,idx); p+=4;
    *p++=0x5A;
    *p++=0x55; *p++=0x8B; *p++=0xEC; *p++=0x51; *p++=0x56;   // push ebp; mov ebp,esp; push ecx; push esi
    *p++=0xE9; { unsigned int next=(unsigned int)(p+4); wr32(p,(unsigned int)(resume-next)); p+=4; }
    return (int)(p-s);
}
static void install_hook(unsigned int target, void* stub){
    DWORD old;
    VirtualProtect((void*)target, 5, PAGE_EXECUTE_READWRITE, &old);
    unsigned char* p=(unsigned char*)target;
    p[0]=0xE9; wr32(p+1,(unsigned int)((unsigned int)stub - (target+5)));
    VirtualProtect((void*)target, 5, old, &old);
    FlushInstructionCache(GetCurrentProcess(),(void*)target,5);
}
static void dump(void){
    if(!g_out[0]) return;
    HANDLE h=CreateFileA(g_out, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0);
    if(h==INVALID_HANDLE_VALUE) return;
    DWORD w;
    unsigned int i0=*g_idx0, i1=*g_idx1;
    WriteFile(h,&i0,4,&w,0); WriteFile(h,&i1,4,&w,0);
    WriteFile(h,g_buf0,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_buf1,sizeof(ENT)*RING,&w,0);
    CloseHandle(h);
}
static DWORD WINAPI worker(LPVOID arg){
    Sleep(2500);
    unsigned int base=(unsigned int)GetModuleHandleA(NULL);
    unsigned int stubsz=96, bufsz=RING*sizeof(ENT);
    unsigned int total=stubsz*2+16+bufsz*2;
    g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!g_mem) return 0;
    unsigned char* stub0=g_mem;
    unsigned char* stub1=g_mem+stubsz;
    g_idx0=(unsigned int*)(g_mem+stubsz*2);
    g_idx1=(unsigned int*)(g_mem+stubsz*2+8);
    g_buf0=(ENT*)(g_mem+stubsz*2+16);
    g_buf1=(ENT*)((unsigned char*)g_buf0+bufsz);
    *g_idx0=0; *g_idx1=0;
    int n0=build_conv(stub0,(unsigned int)g_idx0,(unsigned int)g_buf0, base+OFF_CONV+5);
    int n1=build_glyph(stub1,(unsigned int)g_idx1,(unsigned int)g_buf1, base+OFF_GLYPH+5);
    install_hook(base+OFF_CONV, stub0);
    install_hook(base+OFF_GLYPH, stub1);
    {
        char exe[MAX_PATH]; GetModuleFileNameA(NULL,exe,MAX_PATH);
        char* s=exe; char* last=exe; for(char* q=exe;*q;q++) if(*q=='\\'||*q=='/') last=q;
        int k=(int)(last-exe); if(k>MAX_PATH-16) k=MAX_PATH-16;
        for(int i=0;i<k;i++) g_out[i]=exe[i];
        const char* suf="\\krcodes.bin"; int j=0; while(suf[j]) g_out[k++]=suf[j++]; g_out[k]=0;
    }
    for(;;){ Sleep(1500); dump(); }
    return 0;
}
BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID r){
    if(reason==DLL_PROCESS_ATTACH){ DisableThreadLibraryCalls(h); CreateThread(0,0,worker,0,0,0); }
    return TRUE;
}
