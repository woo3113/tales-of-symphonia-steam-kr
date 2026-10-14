// logger3: patch char-length rule (0x57A8DA) to accept EUC-KR as 2-byte, and log converter
#include <windows.h>
#define RING 1024
#define MASK (RING-1)
#define OFF_LEN   0x17A8DA
#define OFF_CONV  0x17A81C
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem; static unsigned int *g_i0,*g_i1; static ENT *g_b0,*g_b1; static char g_out[MAX_PATH]={0};
static void w32(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static int b_len(unsigned char* s,unsigned int resume1,unsigned int resume2){unsigned char*p=s;
 *p++=0x8D;*p++=0x86;*p++=0xFF;*p++=0x7E;*p++=0x00;*p++=0x00;      // lea eax,[esi+0x7eff]
 *p++=0xBA;w32(p,0xFE);p+=4;                                       // mov edx,0xFE
 *p++=0x66;*p++=0x3B;*p++=0xC2;                                    // cmp ax,dx
 *p++=0x76;{int at=(int)(p-s);p++;}                                 // jbe L2
 *p++=0x8B;*p++=0xC6;                                              // mov eax,esi
 *p++=0x25;w32(p,0xFFFF);p+=4;                                     // and eax,0xFFFF
 *p++=0x2D;w32(p,0xB0A1);p+=4;                                     // sub eax,0xB0A1
 *p++=0x3D;w32(p,0x185D);p+=4;                                     // cmp eax,0x185D
 *p++=0x76;{int at=(int)(p-s);p++;}                                 // jbe L2
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(resume1-n));p+=4;} // jmp len1
 int L2=(int)(p-s);
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(resume2-n));p+=4;} // jmp len2
 s[14+1]= (unsigned char)(L2-16);
 s[33+1]= (unsigned char)(L2-35);
 return (int)(p-s);
}
static int b_conv(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume){unsigned char*p=s;
 *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,idx);p+=4; *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,buf);p+=4;
 *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,buf+4);p+=4;
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,idx);p+=4;
 *p++=0x5A; *p++=0xB9;w32(p,0x80);p+=4; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static int b_glyph(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume){unsigned char*p=s;
 *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,idx);p+=4; *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,buf);p+=4;
 *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,buf+4);p+=4;
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,idx);p+=4;
 *p++=0x5A; *p++=0x55;*p++=0x8B;*p++=0xEC;*p++=0x51;*p++=0x56;
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static void inst(unsigned int t,void* st,int len){DWORD o;VirtualProtect((void*)t,len,PAGE_EXECUTE_READWRITE,&o);unsigned char*p=(unsigned char*)t;p[0]=0xE9;w32(p+1,(unsigned int)((unsigned int)st-(t+5)));VirtualProtect((void*)t,len,o,&o);FlushInstructionCache(GetCurrentProcess(),(void*)t,len);}
static void dump(void){ if(!g_out[0])return; HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0); if(h==INVALID_HANDLE_VALUE)return; DWORD w;
 unsigned int i0=*g_i0,i1=*g_i1; WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0); WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b1,sizeof(ENT)*RING,&w,0); CloseHandle(h);}
static DWORD WINAPI worker(LPVOID a){ Sleep(2500); unsigned int base=(unsigned int)GetModuleHandleA(NULL);
 unsigned int ss=96, bs=RING*sizeof(ENT); unsigned int total=ss*3+16+bs*2;
 g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE); if(!g_mem)return 0;
 unsigned char* s0=g_mem; unsigned char* s1=g_mem+ss; unsigned char* s2=g_mem+ss*2;
 g_i0=(unsigned int*)(g_mem+ss*3); g_i1=g_i0+1; g_b0=(ENT*)(g_mem+ss*3+16); g_b1=(ENT*)((unsigned char*)g_b0+bs);
 *g_i0=0;*g_i1=0;
 b_len(s0, base+0x57A923, base+0x57A8EA);
 b_conv(s1,(unsigned int)g_i0,(unsigned int)g_b0, base+OFF_CONV+5);
 b_glyph(s2,(unsigned int)g_i1,(unsigned int)g_b1, base+0x178680+5);
 inst(base+OFF_LEN, s0, 6);
 inst(base+OFF_CONV, s1, 6);
 inst(base+0x178680, s2, 6);
 { char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH); char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q; int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i]; const char* su="\\krcodes.bin"; for(int j=0;su[j];j++)g_out[k++]=su[j]; g_out[k]=0; }
 for(;;){Sleep(1500);dump();} }
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){ if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);} return TRUE; }
