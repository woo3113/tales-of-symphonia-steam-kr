// 32-bit logging DLL v2: also logs text pointers passed to layout loop (0x57A880)
#include <windows.h>
#define RING 1024
#define MASK (RING-1)
#define OFF_CONV  0x17A81C
#define OFF_GLYPH 0x178680
#define OFF_TEXT  0x17A880
typedef struct { unsigned int a, b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_idx0,*g_idx1,*g_idx2;
static ENT *g_buf0,*g_buf1; static unsigned int* g_ptr2;
static char g_out[MAX_PATH]={0};
static void wr32(unsigned char* p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static int b_conv(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume){unsigned char* p=s;
 *p++=0x52; *p++=0x8B;*p++=0x15;wr32(p,idx);p+=4; *p++=0x89;*p++=0x04;*p++=0xD5;wr32(p,buf);p+=4;
 *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;wr32(p,buf+4);p+=4;
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;wr32(p,MASK);p+=4; *p++=0x89;*p++=0x15;wr32(p,idx);p+=4;
 *p++=0x5A; *p++=0xB9;wr32(p,0x80);p+=4; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);wr32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static int b_glyph(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume){unsigned char* p=s;
 *p++=0x52; *p++=0x8B;*p++=0x15;wr32(p,idx);p+=4; *p++=0x89;*p++=0x04;*p++=0xD5;wr32(p,buf);p+=4;
 *p++=0x89;*p++=0x0C;*p++=0xD5;wr32(p,buf+4);p+=4;
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;wr32(p,MASK);p+=4; *p++=0x89;*p++=0x15;wr32(p,idx);p+=4;
 *p++=0x5A; *p++=0x55;*p++=0x8B;*p++=0xEC;*p++=0x51;*p++=0x56;
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);wr32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static int b_text(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume){unsigned char* p=s;
 *p++=0x8B;*p++=0x44;*p++=0x24;*p++=0x04;              // mov eax,[esp+4]
 *p++=0x8B;*p++=0x15;wr32(p,idx);p+=4;
 *p++=0x89;*p++=0x04;*p++=0x95;wr32(p,buf);p+=4;        // mov [edx*4+buf],eax
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;wr32(p,MASK);p+=4; *p++=0x89;*p++=0x15;wr32(p,idx);p+=4;
 *p++=0x55;*p++=0x8B;*p++=0xEC;*p++=0x83;*p++=0xEC;*p++=0x54;
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);wr32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static void install(unsigned int t,void* stub){DWORD o;VirtualProtect((void*)t,6,PAGE_EXECUTE_READWRITE,&o);unsigned char* p=(unsigned char*)t;p[0]=0xE9;wr32(p+1,(unsigned int)((unsigned int)stub-(t+5)));VirtualProtect((void*)t,6,o,&o);FlushInstructionCache(GetCurrentProcess(),(void*)t,6);}
static void dump(void){ if(!g_out[0])return; HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0); if(h==INVALID_HANDLE_VALUE)return; DWORD w;
 unsigned int i0=*g_idx0,i1=*g_idx1,i2=*g_idx2; WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0);WriteFile(h,&i2,4,&w,0);
 WriteFile(h,g_buf0,sizeof(ENT)*RING,&w,0); WriteFile(h,g_buf1,sizeof(ENT)*RING,&w,0); WriteFile(h,g_ptr2,sizeof(unsigned int)*RING,&w,0); CloseHandle(h);}
static DWORD WINAPI worker(LPVOID a){ Sleep(2500); unsigned int base=(unsigned int)GetModuleHandleA(NULL);
 unsigned int stubsz=96, bs=RING*sizeof(ENT), ps=RING*4;
 unsigned int total=stubsz*3+24+bs*2+ps;
 g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE); if(!g_mem)return 0;
 unsigned char* s0=g_mem; unsigned char* s1=g_mem+stubsz; unsigned char* s2=g_mem+stubsz*2;
 g_idx0=(unsigned int*)(g_mem+stubsz*3); g_idx1=g_idx0+1; g_idx2=g_idx0+2;
 g_buf0=(ENT*)(g_mem+stubsz*3+24); g_buf1=(ENT*)((unsigned char*)g_buf0+bs); g_ptr2=(unsigned int*)((unsigned char*)g_buf1+bs);
 *g_idx0=0;*g_idx1=0;*g_idx2=0;
 b_conv(s0,(unsigned int)g_idx0,(unsigned int)g_buf0, base+OFF_CONV+5);
 b_glyph(s1,(unsigned int)g_idx1,(unsigned int)g_buf1, base+OFF_GLYPH+5);
 b_text(s2,(unsigned int)g_idx2,(unsigned int)g_ptr2, base+OFF_TEXT+6);
 install(base+OFF_CONV,s0); install(base+OFF_GLYPH,s1); install(base+OFF_TEXT,s2);
 { char exe[MAX_PATH];GetModuleFileNameA(NULL,exe,MAX_PATH); char* last=exe; for(char* q=exe;*q;q++) if(*q=='\\'||*q=='/') last=q; int k=(int)(last-exe); for(int i=0;i<k;i++)g_out[i]=exe[i]; const char* suf="\\krcodes.bin"; for(int j=0;suf[j];j++)g_out[k++]=suf[j]; g_out[k]=0; }
 for(;;){Sleep(1500);dump();} }
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){ if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);} return TRUE; }
