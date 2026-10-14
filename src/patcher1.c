// patcher1: patch ALL length-rule sites (lea reg,[code+0x7EFF]...ja) -> code>=0x8101 => 2 bytes.
// log converter inputs too.
#include <windows.h>
#define RING 4096
#define MASK (RING-1)
typedef struct { unsigned int a,b; } ENT;
#define STUBMAX 64
static unsigned char* g_stubs;
static unsigned int* g_i0; static ENT* g_b0; static char g_out[MAX_PATH]={0};
static int g_nsites=0;
static void w32(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static void dump(void){ if(!g_out[0])return; HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0); if(h==INVALID_HANDLE_VALUE)return; DWORD w;
 unsigned int i0=*g_i0, ns=g_nsites; WriteFile(h,&i0,4,&w,0);WriteFile(h,&ns,4,&w,0); WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0); CloseHandle(h);}
static DWORD WINAPI worker(LPVOID a){
 Sleep(120);
 unsigned int base=(unsigned int)GetModuleHandleA(NULL);
 unsigned int bs=RING*sizeof(ENT);
 unsigned int total=0x2000 + 16 + bs;                 // stubs + idx + buffer
 unsigned char* mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
 g_stubs=mem; g_i0=(unsigned int*)(mem+0x2000); g_b0=(ENT*)(mem+0x2010); *g_i0=0;
 unsigned char* t=(unsigned char*)(base+0x1000); unsigned int tsize=0x301185;
 int site=0;
 for(unsigned int k=0;k+16<tsize;k++){
   if(!(t[k]==0x8D && t[k+2]==0xFF && t[k+3]==0x7E && t[k+4]==0x00 && t[k+5]==0x00)) continue;
   unsigned char modrm=t[k+1]; int mod=modrm>>6, rm=modrm&7;
   if(mod!=0x2 || rm==4) continue;
   int R=rm;
   unsigned int st=base+0x1000+k;
   // find ja within [k+11, k+20]
   int jaoff=-1; unsigned int len1=0,len2=0;
   for(int d=11; d<=20; d++){
     unsigned char c=t[k+d];
     if(c==0x77){ jaoff=d; len1=st+d+2+(signed char)t[k+d+1]; len2=st+d+2; break; }
     if(c==0x0F && t[k+d+1]==0x87){ int r; memcpy(&r,t+k+d+2,4); jaoff=d; len1=st+d+6+r; len2=st+d+6; break; }
   }
   if(jaoff<0) continue;
   unsigned char* s=g_stubs+site*STUBMAX;
   unsigned char* p=s;
   *p++=0x66; *p++=0x81; *p++=(unsigned char)(0xF8|R);
   *p++=0x01; *p++=0x81;                       // cmp r16,0x8101
   *p++=0x72; *p++=0x05;                       // jb L1
   { *p++=0xE9; unsigned int n=(unsigned int)(p+4); w32(p,(unsigned int)(len2-n)); p+=4; }
   { *p++=0xE9; unsigned int n=(unsigned int)(p+4); w32(p,(unsigned int)(len1-n)); p+=4; }
   // hook site
   DWORD o; VirtualProtect((void*)st,6,PAGE_EXECUTE_READWRITE,&o);
   ((unsigned char*)st)[0]=0xE9; w32((unsigned char*)st+1,(unsigned int)((unsigned int)s-(st+5)));
   VirtualProtect((void*)st,6,o,&o); FlushInstructionCache(GetCurrentProcess(),(void*)st,6);
   site++;
   if(site>=120) break;
 }
 g_nsites=site;
 // converter log hook (place after stubs)
 unsigned char* s=g_stubs+120*STUBMAX;
 { unsigned char* p=s;
   *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,(unsigned int)g_b0);p+=4;
   *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,(unsigned int)g_b0+4);p+=4;
   *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x5A; *p++=0xB9;w32(p,0x80);p+=4; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)((base+0x57A81C+5)-n));p+=4;} }
 { DWORD o; unsigned int tgt=base+0x17A81C; VirtualProtect((void*)tgt,6,PAGE_EXECUTE_READWRITE,&o); ((unsigned char*)tgt)[0]=0xE9; w32((unsigned char*)tgt+1,(unsigned int)((unsigned int)s-(tgt+5))); VirtualProtect((void*)tgt,6,o,&o); FlushInstructionCache(GetCurrentProcess(),(void*)tgt,6); }
 { char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH); char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q; int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i]; const char* su="\\krcodes.bin"; for(int j=0;su[j];j++)g_out[k++]=su[j]; g_out[k]=0; }
 for(;;){Sleep(1500);dump();}
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){ if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);} return TRUE; }
