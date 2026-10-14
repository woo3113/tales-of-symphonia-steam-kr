// logger8: full B-pipeline prototype (v2, corrected branch targets).
//   - 26 length-rule sites: EUC-KR reads as 2 bytes
//   - 5 converter copies: EUC-KR -> glyph 0x4000 + idx  (idx=(b0-0xB0)*94+(b1-0xA1))
//   - glyph slot 0x578680: ax in [0x4000,0x4000+N) -> group=2+idx/192, slot=idx%192
//   - width 0x57ACD0: Korean -> 48
//   - taps main loop 0x57A8B0 and logs Korean converter hits.
#include <windows.h>
#include "lensites.h"

#define RING 4096
#define MASK (RING-1)
#define GBASE 0x4000
#define GCOUNT 2445
#define GPAGEOFF 2
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_i0, *g_ik;
static ENT *g_b0, *g_bk;
static char g_out[MAX_PATH]={0};

static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EW(unsigned char*p,unsigned short v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);return p+2;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE9);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
static void fixj(unsigned char* op,unsigned char* tgt){*op=(unsigned char)(tgt-(op+1));}

// EUC-KR Hangul test on the 16-bit code in Rw. Sets *JA/*JB to the two `ja` operand
// addresses (taken when NOT Korean). clobbers eax,ecx.
static unsigned char* KORTEST(unsigned char* p,unsigned char R,unsigned char** JA,unsigned char** JB){
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);        // movzx eax,Rw
    p=EB(p,0x8B);p=EB(p,0xC8);                        // mov ecx,eax
    p=EB(p,0xC1);p=EB(p,0xE9);p=EB(p,0x08);           // shr ecx,8
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xB0);           // sub ecx,0xB0
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0x18);           // cmp ecx,0x18
    p=EB(p,0x77); *JA=p; p=EB(p,0x00);                // ja NOT_KR
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0xC8);           // movzx ecx,al
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xA1);           // sub ecx,0xA1
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0x5D);           // cmp ecx,0x5D
    p=EB(p,0x77); *JB=p; p=EB(p,0x00);                // ja NOT_KR
    return p;
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
static unsigned char* stub_len(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_len2,unsigned int r_resume,unsigned int base){
    unsigned char *ja,*jb,*Lorig;
    p=EB(p,0x50);                                   // push eax
    p=KORTEST(p,R,&ja,&jb);
    p=EB(p,0x58);                                   // pop eax
    p=EJMP(p, base+r_len2);                         // korean -> len2
    Lorig=p; fixj(ja,Lorig); fixj(jb,Lorig);
    p=EB(p,0x58);                                   // pop eax
    p=EB(p,0xB8|R3); p=EI(p,0xFE);                  // mov R3,0xFE (replay)
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_conv(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_resume,unsigned int r_end,int is_ret,unsigned int base,unsigned int idxb,unsigned int buf){
    unsigned char *ja,*jb,*Lorig;
    p=EB(p,0x50);                                   // push eax
    p=KORTEST(p,R,&ja,&jb);
    // korean path
    p=EB(p,0x52);p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idxb);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x8B);p=EB(p,0x4C);p=EB(p,0x24);p=EB(p,0x04);   // mov ecx,[esp+4] (saved eax)
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idxb);
    p=EB(p,0x5A);                                   // pop edx
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);       // movzx eax,Rw
    p=EB(p,0x8B);p=EB(p,0xC8);                      // mov ecx,eax
    p=EB(p,0xC1);p=EB(p,0xE9);p=EB(p,0x08);         // shr ecx,8
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xB0);         // sub ecx,0xB0
    p=EB(p,0x6B);p=EB(p,0xC9);p=EB(p,94);           // imul ecx,ecx,94
    p=EB(p,0x25);p=EI(p,0xFF);                      // and eax,0xFF
    p=EB(p,0x2D);p=EI(p,0xA1);                      // sub eax,0xA1
    p=EB(p,0x03);p=EB(p,0xC8);                      // add ecx,eax
    p=EB(p,0x81);p=EB(p,0xC1);p=EI(p,GBASE);        // add ecx,0x4000
    p=EB(p,0x8B);p=EB(p,0xC1);                      // mov eax,ecx
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);         // add esp,4
    if(is_ret){ p=EB(p,0xC3); } else { p=EJMP(p, base+r_end); }
    Lorig=p; fixj(ja,Lorig); fixj(jb,Lorig);
    p=EB(p,0x58);                                   // pop eax
    p=EB(p,0xB8|R3); p=EI(p,0x80);                  // mov R3,0x80 (replay)
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_width(unsigned char* p,unsigned int base){
    unsigned char *ja,*jb,*Lorig;
    p=EB(p,0x50);
    p=KORTEST(p,0,&ja,&jb);
    p=EB(p,0x58);
    p=EB(p,0xB8);p=EI(p,0x30);                      // mov eax,48
    p=EB(p,0xC3);                                   // ret
    Lorig=p; fixj(ja,Lorig); fixj(jb,Lorig);
    p=EB(p,0x58);
    p=EB(p,0x8B);p=EB(p,0xC1);                      // mov ecx,eax (replay)
    p=EB(p,0x81);p=EB(p,0xE1);p=EI(p,0xFF00);       // and ecx,0xff00
    p=EJMP(p, base+0x17ACD8);
    return p;
}
static unsigned char* stub_glyph(unsigned char* p,unsigned int base){
    p=EB(p,0x66);p=EB(p,0x3D);p=EW(p,GBASE);            // cmp ax,0x4000
    p=EB(p,0x72); unsigned char* j1=p; p=EB(p,0x00);    // jb L_orig
    p=EB(p,0x66);p=EB(p,0x3D);p=EW(p,GBASE+GCOUNT);     // cmp ax,0x4000+N
    p=EB(p,0x73); unsigned char* j2=p; p=EB(p,0x00);    // jae L_orig
    p=EB(p,0x51);                                       // push ecx (ctx)
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0);             // movzx eax,ax
    p=EB(p,0x2D);p=EI(p,GBASE);                         // sub eax,0x4000
    p=EB(p,0x33);p=EB(p,0xD2);                          // xor edx,edx
    p=EB(p,0xB9);p=EI(p,192);                           // mov ecx,192
    p=EB(p,0xF7);p=EB(p,0xF1);                          // div ecx
    p=EB(p,0x8B);p=EB(p,0xCA);                          // mov ecx,edx (slot)
    p=EB(p,0x5A);                                       // pop edx (ctx)
    p=EB(p,0x83);p=EB(p,0xC0);p=EB(p,GPAGEOFF);         // add eax,GPAGEOFF (group)
    p=EB(p,0x55);p=EB(p,0x8B);p=EB(p,0xEC);             // push ebp; mov ebp,esp
    p=EB(p,0x52);                                       // push edx
    p=EB(p,0x56);                                       // push esi
    p=EB(p,0x8B);p=EB(p,0xF2);                          // mov esi,edx
    p=EB(p,0x85);p=EB(p,0xF6);                          // test esi,esi
    p=EB(p,0x75);p=EB(p,0x05);                          // jne +5
    p=EB(p,0xBE);p=EI(p,0xB190A0);                      // mov esi,0xb190a0
    p=EJMP(p, base+0x178737);
    unsigned char* Lo=p;
    p=EB(p,0x55);p=EB(p,0x8B);p=EB(p,0xEC);p=EB(p,0x51);p=EB(p,0x56);
    p=EJMP(p, base+0x178685);
    fixj(j1,Lo); fixj(j2,Lo);
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
    unsigned int i0=*g_i0, ik=*g_ik;
    WriteFile(h,&i0,4,&w,0);WriteFile(h,&ik,4,&w,0);
    WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_bk,sizeof(ENT)*RING,&w,0);
    CloseHandle(h);
}
static DWORD WINAPI worker(LPVOID a){
    (void)a;
    Sleep(60);
    unsigned int base=(unsigned int)GetModuleHandleA(NULL);
    unsigned int ss=224, bs=RING*sizeof(ENT);
    unsigned int nstub=1+1+1+5+N_LS;   // loop tap + glyph + width + conv + len
    unsigned int total=ss*nstub+16+bs*2+16;
    g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!g_mem)return 0;
    unsigned char* s0=g_mem;
    unsigned char* sglyph=g_mem+ss;
    unsigned char* swidth=g_mem+ss*2;
    unsigned char* sconv=g_mem+ss*3;
    g_i0=(unsigned int*)(g_mem+ss*nstub); g_ik=g_i0+1;
    g_b0=(ENT*)(g_mem+ss*nstub+16);
    g_bk=(ENT*)((unsigned char*)g_b0+bs);
    *g_i0=0; *g_ik=0;
    { unsigned char* p=stub_bytes(s0,(unsigned int)g_i0,(unsigned int)g_b0,
        (unsigned char[]){0xDD,0x05,0x30,0x2A,0x88,0x00},6, base+0x17A8B6); (void)p; patch(base+0x17A8B0, s0, 6); }
    { stub_glyph(sglyph, base); patch(base+0x178680, sglyph, 6); }
    { stub_width(swidth, base); patch(base+0x17ACD0, swidth, 8); }
    { stub_conv(sconv+0*ss, 0, 1, 0x17A821, 0, 1, base, (unsigned int)g_ik, (unsigned int)g_bk); patch(base+0x17A81C, sconv+0*ss, 5); }
    { stub_conv(sconv+1*ss, 6, 1, 0x17A995, 0x17A9E4, 0, base, (unsigned int)g_ik, (unsigned int)g_bk); patch(base+0x17A990, sconv+1*ss, 5); }
    { stub_conv(sconv+2*ss, 6, 1, 0x154E23, 0x154E72, 0, base, (unsigned int)g_ik, (unsigned int)g_bk); patch(base+0x154E1E, sconv+2*ss, 5); }
    { stub_conv(sconv+3*ss, 0, 2, 0x157BAA, 0x157C04, 0, base, (unsigned int)g_ik, (unsigned int)g_bk); patch(base+0x157BA5, sconv+3*ss, 5); }
    { stub_conv(sconv+4*ss, 0, 2, 0x13880E, 0x138868, 0, base, (unsigned int)g_ik, (unsigned int)g_bk); patch(base+0x138809, sconv+4*ss, 5); }
    for(int i=0;i<N_LS;i++){
        unsigned char* st=g_mem+ss*(8+i);
        stub_len(st, g_ls[i].R, g_ls[i].R3, g_ls[i].len2, g_ls[i].patch+5, base);
        patch(base+g_ls[i].patch, st, 5);
    }
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
