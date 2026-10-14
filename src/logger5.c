// logger5: FIXED length-rule patch (EUC-KR -> 2byte) + conv/glyph/width logging
#include <windows.h>
#define RING 1024
#define MASK (RING-1)
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem; static unsigned int *g_i0,*g_i1,*g_i2; static ENT *g_b0,*g_b1,*g_b2; static char g_out[MAX_PATH]={0};
static void w32(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static int b_len(unsigned char* s,unsigned int r1,unsigned int r2){unsigned char*p=s;
 *p++=0x8D;*p++=0x86;*p++=0xFF;*p++=0x7E;*p++=0x00;*p++=0x00;   // lea eax,[esi+0x7eff]
 *p++=0xBA;w32(p,0xFE);p+=4;                                    // mov edx,0xFE
 *p++=0x66;*p++=0x3B;*p++=0xC2;                                 // cmp ax,dx
 *p++=0x76;p++;                                                 // jbe L2 (op@14, opnd@15)
 *p++=0x8B;*p++=0xC6;                                           // mov eax,esi
 *p++=0x25;w32(p,0xFFFF);p+=4;                                  // and eax,0xFFFF
 *p++=0x2D;w32(p,0xB0A1);p+=4;                                  // sub eax,0xB0A1
 *p++=0x3D;w32(p,0x185D);p+=4;                                  // cmp eax,0x185D
 *p++=0x76;p++;                                                 // jbe L2 (op@36, opnd@37)
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(r1-n));p+=4;}  // jmp len1 (off 38)
 int L2=(int)(p-s);                                             // 43
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(r2-n));p+=4;}  // jmp len2
 s[15]=(unsigned char)(L2-16);
 s[37]=(unsigned char)(L2-38);
 return (int)(p-s);}
static int b_ent(unsigned char* s,unsigned int idx,unsigned int buf,unsigned int resume,unsigned char const* rep,int replen){unsigned char*p=s;
 *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,idx);p+=4; *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,buf);p+=4;
 *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,buf+4);p+=4;
 *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,idx);p+=4;
 *p++=0x5A; for(int i=0;i<replen;i++)*p++=rep[i];
 *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)(resume-n));p+=4;} return (int)(p-s);}
static void inst(unsigned int t,void* st,int len){DWORD o;VirtualProtect((void*)t,len,PAGE_EXECUTE_READWRITE,&o);unsigned char*p=(unsigned char*)t;p[0]=0xE9;w32(p+1,(unsigned int)((unsigned int)st-(t+5)));VirtualProtect((void*)t,len,o,&o);FlushInstructionCache(GetCurrentProcess(),(void*)t,len);}
static void dump(void){ if(!g_out[0])return; HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0); if(h==INVALID_HANDLE_VALUE)return; DWORD w;
 unsigned int i0=*g_i0,i1=*g_i1,i2=*g_i2; WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0);WriteFile(h,&i2,4,&w,0);
 WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b1,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b2,sizeof(ENT)*RING,&w,0);CloseHandle(h);}
static DWORD WINAPI worker(LPVOID a){ Sleep(2500); unsigned int base=(unsigned int)GetModuleHandleA(NULL);
 unsigned int ss=128, bs=RING*sizeof(ENT); unsigned int total=ss*4+16+bs*3;
 g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE); if(!g_mem)return 0;
 unsigned char* s0=g_mem,*s1=g_mem+ss,*s2=g_mem+ss*2,*s3=g_mem+ss*3;
 g_i0=(unsigned int*)(g_mem+ss*4); g_i1=g_i0+1; g_i2=g_i0+2; g_b0=(ENT*)(g_mem+ss*4+16); g_b1=(ENT*)((unsigned char*)g_b0+bs); g_b2=(ENT*)((unsigned char*)g_b1+bs);
 *g_i0=0;*g_i1=0;*g_i2=0;
 b_len(s0, base+0x57A923, base+0x57A8EA);
 b_ent(s1,(unsigned int)g_i0,(unsigned int)g_b0, base+0x57A81C+5, (unsigned char[]){0x52,0x8B,0x15,0,0,0,0}, 0); // placeholder not used
 b_ent(s1,(unsigned int)g_i0,(unsigned int)g_b0, base+0x57A81C+5, (unsigned char[]){0x00}, 0);
 /* conv hook: log eax + [esp+4] then mov ecx,0x80 */
 { unsigned char* p=s1; *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,(unsigned int)g_b0);p+=4;
   *p++=0x8B;*p++=0x4C;*p++=0x24;*p++=0x04; *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,(unsigned int)g_b0+4);p+=4;
   *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,(unsigned int)g_i0);p+=4;
   *p++=0x5A; *p++=0xB9;w32(p,0x80);p+=4; *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)((base+0x57A81C+5)-n));p+=4;} }
 /* glyph hook: log eax + ecx then 55 8B EC 51 56 */
 { unsigned char* p=s2; *p++=0x52; *p++=0x8B;*p++=0x15;w32(p,(unsigned int)g_i1);p+=4;
   *p++=0x89;*p++=0x04;*p++=0xD5;w32(p,(unsigned int)g_b1);p+=4;
   *p++=0x89;*p++=0x0C;*p++=0xD5;w32(p,(unsigned int)g_b1+4);p+=4;
   *p++=0x83;*p++=0xC2;*p++=0x01; *p++=0x81;*p++=0xE2;w32(p,MASK);p+=4; *p++=0x89;*p++=0x15;w32(p,(unsigned int)g_i1);p+=4;
   *p++=0x5A; *p++=0x55;*p++=0x8B;*p++=0xEC;*p++=0x51;*p++=0x56;
   *p++=0xE9;{unsigned int n=(unsigned int)(p+4);w32(p,(unsigned int)((base+0x178680+5)-n));p+=4;} }
 /* width hook: log eax + [esp+4] then 8B C1 81 E1 00 FF 00 00 */
 b_ent(s3,(unsigned int)g_i2,(unsigned int)g_b2, base+0x57ACD0+8, (unsigned char[]){0x8B,0xC1,0x81,0xE1,0x00,0xFF,0x00,0x00}, 8);
 inst(base+0x17A8DA, s0, 6);
 inst(base+0x57A81C, s1, 6);
 inst(base+0x178680, s2, 6);
 inst(base+0x57ACD0, s3, 8);
 { char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH); char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q; int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i]; const char* su="\\krcodes.bin"; for(int j=0;su[j];j++)g_out[k++]=su[j]; g_out[k]=0; }
 for(;;){Sleep(1500);dump();} }
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){ if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);} return TRUE; }
