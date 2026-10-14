// logger7: patches ALL 26 length-rule sites so EUC-KR (0xB0A1..0xC8FE) reads as 2 bytes,
//          while keeping original 1-byte behaviour for ASCII etc.
//          Also taps main loop / width / glyph / converter for verification.
#include <windows.h>
#include "lensites.h"

#define RING 4096
#define MASK (RING-1)
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_i0,*g_i1,*g_i2,*g_i3;
static ENT *g_b0,*g_b1,*g_b2,*g_b3;
static char g_out[MAX_PATH]={0};
static volatile int g_npatched=0;

static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){
    unsigned char* q=EB(p,0xE9); unsigned int next=(unsigned int)(q+4);
    return EI(q,(unsigned int)(tgt-next));
}
static unsigned char* stub_ret(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52); p=EB(p,0x51);
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x8B);p=EB(p,0x4C);p=EB(p,0x24);p=EB(p,0x08);
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x59); p=EB(p,0x5A);
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    return EJMP(p,resume);
}
static unsigned char* stub_ecx(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52); p=EB(p,0x51);
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x59); p=EB(p,0x5A);
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    return EJMP(p,resume);
}
static unsigned char* stub_bytes(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52); p=EB(p,0x51);
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x8B);p=EB(p,0x08);
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x59); p=EB(p,0x5A);
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    return EJMP(p,resume);
}
// patched over `mov R3,0xFE` (5 bytes)
static unsigned char* stub_len(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_len2,unsigned int r_resume,unsigned int base){
    // movzx eax, Rw : 0F B7 (C0|R)
    p=EB(p,0x50);                                  // push eax
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);      // movzx eax,Rw
    p=EB(p,0x2D);p=EI(p,0xB0A1);                   // sub eax,0xB0A1
    p=EB(p,0x3D);p=EI(p,0x185D);                   // cmp eax,0x185D
    p=EB(p,0x76); unsigned char* jk=p; p=EB(p,0x00);// jbe L_kr
    p=EB(p,0x58);                                  // pop eax
    p=EB(p,0xB8|R3); p=EI(p,0xFE);                 // mov R3,0xFE
    p=EJMP(p, base+r_resume);                      // jmp resume
    unsigned char* Lk=p;
    p=EB(p,0x58);                                  // pop eax
    p=EJMP(p, base+r_len2);                        // jmp len2
    *jk=(unsigned char)(Lk-(jk+1));
    return p;
}
static void patch(unsigned int t,unsigned char* st,int len){
    DWORD o; VirtualProtect((void*)t,len,PAGE_EXECUTE_READWRITE,&o);
    unsigned char* p=(unsigned char*)t;
    p[0]=0xE9; EI(p+1,(unsigned int)((unsigned int)st-(t+5)));
    VirtualProtect((void*)t,len,o,&o);
    FlushInstructionCache(GetCurrentProcess(),(void*)t,len);
}
static void dump(void){
    if(!g_out[0])return;
    HANDLE h=CreateFileA(g_out,GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
    if(h==INVALID_HANDLE_VALUE)return; DWORD w;
    unsigned int i0=*g_i0,i1=*g_i1,i2=*g_i2,i3=*g_i3,np=(unsigned int)g_npatched;
    WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0);WriteFile(h,&i2,4,&w,0);WriteFile(h,&i3,4,&w,0);
    WriteFile(h,&np,4,&w,0);
    WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b1,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_b2,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b3,sizeof(ENT)*RING,&w,0);
    CloseHandle(h);
}
static DWORD WINAPI worker(LPVOID a){
    (void)a;
    Sleep(60);
    unsigned int base=(unsigned int)GetModuleHandleA(NULL);
    unsigned int ss=192, bs=RING*sizeof(ENT);
    unsigned int nstub=4+N_LS;
    unsigned int total=ss*nstub+16+bs*4;
    g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!g_mem)return 0;
    unsigned char* s0=g_mem, *s1=g_mem+ss, *s2=g_mem+ss*2, *s3=g_mem+ss*3;
    g_i0=(unsigned int*)(g_mem+ss*nstub); g_i1=g_i0+1; g_i2=g_i0+2; g_i3=g_i0+3;
    g_b0=(ENT*)(g_mem+ss*nstub+16);
    g_b1=(ENT*)((unsigned char*)g_b0+bs);
    g_b2=(ENT*)((unsigned char*)g_b1+bs);
    g_b3=(ENT*)((unsigned char*)g_b2+bs);
    *g_i0=*g_i1=*g_i2=*g_i3=0;
    // taps
    { unsigned char* p=stub_bytes(s0,(unsigned int)g_i0,(unsigned int)g_b0,
        (unsigned char[]){0xDD,0x05,0x30,0x2A,0x88,0x00},6, base+0x17A8B6); (void)p; patch(base+0x17A8B0, s0, 6); }
    { unsigned char* p=stub_ret(s1,(unsigned int)g_i1,(unsigned int)g_b1,
        (unsigned char[]){0x8B,0xC1,0x81,0xE1,0x00,0xFF,0x00,0x00},8, base+0x17ACD8); (void)p; patch(base+0x17ACD0, s1, 8); }
    { unsigned char* p=stub_ecx(s2,(unsigned int)g_i2,(unsigned int)g_b2,
        (unsigned char[]){0x55,0x8B,0xEC,0x51,0x56},5, base+0x178685); (void)p; patch(base+0x178680, s2, 5); }
    { unsigned char* p=stub_ret(s3,(unsigned int)g_i3,(unsigned int)g_b3,
        (unsigned char[]){0xB9,0x80,0x00,0x00,0x00},5, base+0x17A821); (void)p; patch(base+0x17A81C, s3, 5); }
    // length rules
    int n=0;
    for(int i=0;i<N_LS;i++){
        unsigned char* st=g_mem+ss*(4+i);
        stub_len(st, g_ls[i].R, g_ls[i].R3, g_ls[i].len2, g_ls[i].patch + 5, base);
        patch(base+g_ls[i].patch, st, 5);
        n++;
    }
    g_npatched=n;
    {
        char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH);
        char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q;
        int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i];
        const char* su="\\krcodes.bin"; for(int j=0;su[j];j++) g_out[k++]=su[j]; g_out[k]=0;
    }
    for(;;){Sleep(1200);dump();}
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){
    if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);}
    (void)h;(void)x;return TRUE;
}
