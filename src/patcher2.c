// patcher2: fix ONLY the draw-loop length rule (0x57A8DA, code in esi) -> code>=0x8101 => 2 bytes.
// hook converter (0x57A81C) + glyph (0x578680) to log.
#include <windows.h>
#define RING 4096
#define MASK (RING-1)
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_stubs; static unsigned int* g_i0; static ENT* g_b0; static unsigned int* g_i1; static ENT* g_b1; static char g_out[MAX_PATH]={0};
static void w32(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static void dump(void){ if(!g_out[0])return; HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0); if(h==INVALID_HANDLE_VALUE)return; DWORD w;
 unsigned int i0=*g_i0,i1=*g_i1; WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0);
 WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0); WriteFile(h,g_b1,sizeof(ENT)*RING,&w,0); CloseHandle(h);}
static void inst(unsigned int tgt,void* st){DWORD o;VirtualProtect((void*)tgt,6,PAGE_EXECUTE_READWRITE,&o);((unsigned char*)tgt)[0]=0xE9;w32((unsigned char*)tgt+1,(unsigned int)((unsigned int)st-(tgt+5)));VirtualProtect((void*)tgt,6,o,&o);FlushInstructionCache(GetCurrentProcess(),(void*)tgt,6);}
static DWORD WINAPI worker(LPVOID a){
 Sleep(120);
 unsigned int base=(unsigned int)GetModuleHandleA(NULL);
 unsigned int bs=RING*sizeof(ENT);
 unsigned int total=0x4000+16+bs*2;
 unsigned char* mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
 g_stubs=mem; g_i0=(unsigned int*)(mem+0x4000); g_i1=g_i0+1; g_b0=(ENT*)(mem+0x4010); g_b1=(ENT*)((unsigned char*)g_b0+bs);
 *g_i0=0;*g_i1=0;
 unsigned int site=base+0x17A8DA;
 unsigned int len1=base+0x17A923, len2=base+0x17A8EA;
 // stub: cmp si,0x8101 ; jb L1 ; jmp len2 ; L1: jmp len1
 { unsigned char* s=g_stubs; unsigned char* p=s;
   *p++=0x66;*p++=0x81;*p++=0xFE; *p++=0x01;*p++=0x81;      // cmp si,0x8101
   *p++=0x72;*p++=0x05;                                       // jb L1
   { *p++=0xE9; unsigned int n=(unsigned int)(p+4); w32(p,(unsigned int)(len2-n)); p+=4; }
   { *p++=0xE9; unsigned int n=(unsigned int)(p+4); w32(p,(unsigned int)(len1-n)); p+=4; } }
 inst(site, g_stubs);
 // converter log hook
 { unsigned char* p=g_stubs+64;
   *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,(unsigned int)g_b0);p+=4;
   *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,(unsigned int)g_b0+4);p+=4;
   *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x5A; *p++=0xB9;w32(p,0x80);p+=4; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)((base+0x57A81C+5)-n));p+=4;}
   inst(base+0x17A81C, g_stubs+64); }
 // glyph log hook
 { unsigned char* p=g_stubs+128;
   *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,(unsigned int)g_i1);p+=4;
   *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,(unsigned int)g_b1);p+=4;
   *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,(unsigned int)g_b1+4);p+=4;
   *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,(unsigned int)g_i1);p+=4;
   *p++=0x5A; *p++=0x55;*p++=0x8B;*p++=0xEC;*p++=0x51;*p++=0x56; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)((base+0x178680+5)-n));p+=4;}
   inst(base+0x178680, g_stubs+128); }
 { char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH); char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q; int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i]; const char* su="\\krcodes.bin"; for(int j=0;su[j];j++)g_out[k++]=su[j]; g_out[k]=0; }
 for(;;){Sleep(1500);dump();}
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){ if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);} return TRUE; }
