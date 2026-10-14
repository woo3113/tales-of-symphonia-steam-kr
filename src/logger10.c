// logger9: PAL_FONTB0-based atlas (4096x4096, 13 pages in a 5x7 grid).
//   - length rules (26), converters (5) : EUC-KR -> 0x4000+idx ; ASCII(0x20..0x7E) -> 0x4000+2350+(c-0x20)
//   - glyph 0x578680 replaced: 0x4000+gi -> grid cell (COL=gpcol*16+c, ROW=gprow*12+r) *48px
//   - width 0x57ACD0 -> 48 for Korean
#include <windows.h>
#include "lensites.h"

#define RING 4096
#define MASK (RING-1)
#define GBASE 0x4000
#define KCOUNT 2350
#define ACOUNT 95
#define GCOUNT (KCOUNT+ACOUNT)     // 2445
#define ASCII_BASE KCOUNT
#define GRID_COLS 5
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_i0, *g_ik;
static ENT *g_b0, *g_bk;
static char g_out[MAX_PATH]={0};

static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EW(unsigned char*p,unsigned short v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);return p+2;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE9);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
static void fixj32(unsigned char* op,unsigned char* tgt){unsigned int r=(unsigned int)(tgt-(op+4));op[0]=(unsigned char)r;op[1]=(unsigned char)(r>>8);op[2]=(unsigned char)(r>>16);op[3]=(unsigned char)(r>>24);}

// EUC-KR test; *JA/*JB = rel32 operand addresses of `jb/jae` to NOT-Korean path.
static unsigned char* KORTEST(unsigned char* p,unsigned char R,unsigned char** JA,unsigned char** JB){
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);
    p=EB(p,0x8B);p=EB(p,0xC8);
    p=EB(p,0xC1);p=EB(p,0xE9);p=EB(p,0x08);
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xB0);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0x18);
    p=EB(p,0x0F);p=EB(p,0x82); *JA=p; p=EI(p,0);      // jb NOT_KR
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0xC8);
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xA1);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0x5D);
    p=EB(p,0x0F);p=EB(p,0x82); *JB=p; p=EI(p,0);      // jb NOT_KR
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
    p=EB(p,0x50);
    p=KORTEST(p,R,&ja,&jb);
    p=EB(p,0x58);
    p=EJMP(p, base+r_len2);
    Lorig=p; fixj32(ja,Lorig); fixj32(jb,Lorig);
    p=EB(p,0x58);
    p=EB(p,0xB8|R3); p=EI(p,0xFE);
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_conv(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_resume,unsigned int r_end,int is_ret,unsigned int base,unsigned int idxb,unsigned int buf){
    unsigned char *ja,*jb,*Lorig,*jA,*jB,*Lnota;
    p=EB(p,0x50);                                   // push eax
    // ASCII 0x20..0x7E -> GBASE+ASCII_BASE+(c-0x20)
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);       // movzx eax,Rw
    p=EB(p,0x3D);p=EI(p,0x20);                        // cmp eax,0x20
    p=EB(p,0x0F);p=EB(p,0x82); jA=p; p=EI(p,0);       // jb NOTA
    p=EB(p,0x3D);p=EI(p,0x7E);                        // cmp eax,0x7E
    p=EB(p,0x0F);p=EB(p,0x87); jB=p; p=EI(p,0);       // ja NOTA
    p=EB(p,0x2D);p=EI(p,0x20);                        // sub eax,0x20
    p=EB(p,0x05);p=EI(p,GBASE+ASCII_BASE);            // add eax,...
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);           // add esp,4
    if(is_ret){ p=EB(p,0xC3); } else { p=EJMP(p, base+r_end); }
    Lnota=p; fixj32(jA,Lnota); fixj32(jB,Lnota);
    p=KORTEST(p,R,&ja,&jb);
    // korean path
    p=EB(p,0x52);p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idxb);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x8B);p=EB(p,0x4C);p=EB(p,0x24);p=EB(p,0x04);
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idxb);
    p=EB(p,0x5A);
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);
    p=EB(p,0x8B);p=EB(p,0xC8);
    p=EB(p,0xC1);p=EB(p,0xE9);p=EB(p,0x08);
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xB0);
    p=EB(p,0x6B);p=EB(p,0xC9);p=EB(p,94);
    p=EB(p,0x25);p=EI(p,0xFF);
    p=EB(p,0x2D);p=EI(p,0xA1);
    p=EB(p,0x03);p=EB(p,0xC8);
    p=EB(p,0x81);p=EB(p,0xC1);p=EI(p,GBASE);
    p=EB(p,0x8B);p=EB(p,0xC1);
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);
    if(is_ret){ p=EB(p,0xC3); } else { p=EJMP(p, base+r_end); }
    Lorig=p; fixj32(ja,Lorig); fixj32(jb,Lorig);
    p=EB(p,0x58);
    p=EB(p,0xB8|R3); p=EI(p,0x80);
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_width(unsigned char* p,unsigned int base){
    unsigned char *ja,*jb,*Lorig;
    p=EB(p,0x50);
    p=KORTEST(p,0,&ja,&jb);
    p=EB(p,0x58);
    p=EB(p,0xB8);p=EI(p,0x30);
    p=EB(p,0xC3);
    Lorig=p; fixj32(ja,Lorig); fixj32(jb,Lorig);
    p=EB(p,0x58);
    p=EB(p,0x8B);p=EB(p,0xC1);
    p=EB(p,0x81);p=EB(p,0xE1);p=EI(p,0xFF00);
    p=EJMP(p, base+0x17ACD8);
    return p;
}
// custom glyph slot: 0x4000+gi -> grid cell coords *48px
static unsigned char* stub_glyph(unsigned char* p,unsigned int base){
    unsigned char *j1,*j2,*Lorig;
    p=EB(p,0x66);p=EB(p,0x3D);p=EW(p,GBASE);              // cmp ax,GBASE
    p=EB(p,0x0F);p=EB(p,0x82); j1=p; p=EI(p,0);           // jb Lorig
    p=EB(p,0x66);p=EB(p,0x3D);p=EW(p,GBASE+GCOUNT);       // cmp ax,GBASE+GCOUNT
    p=EB(p,0x0F);p=EB(p,0x83); j2=p; p=EI(p,0);           // jae Lorig
    p=EB(p,0x55);p=EB(p,0x8B);p=EB(p,0xEC);             // push ebp; mov ebp,esp
    p=EB(p,0x51);p=EB(p,0x56);p=EB(p,0x53);p=EB(p,0x57); // push ecx;push esi;push ebx;push edi
    p=EB(p,0x8B);p=EB(p,0xF1);                          // mov esi,ecx
    p=EB(p,0x85);p=EB(p,0xF6);                          // test esi,esi
    p=EB(p,0x75);p=EB(p,0x05);                          // jne +5
    p=EB(p,0xBE);p=EI(p,0xB190A0);                        // mov esi,0xb190a0
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0);             // movzx eax,ax
    p=EB(p,0x2D);p=EI(p,GBASE);                           // sub eax,GBASE
    p=EB(p,0x33);p=EB(p,0xD2);                          // xor edx,edx
    p=EB(p,0xB9);p=EI(p,192);                             // mov ecx,192
    p=EB(p,0xF7);p=EB(p,0xF1);                          // div ecx  -> eax=page, edx=cell
    p=EB(p,0x8B);p=EB(p,0xF8);                          // mov edi,eax (page)
    p=EB(p,0x8B);p=EB(p,0xDA);                          // mov ebx,edx (cell)
    p=EB(p,0x8B);p=EB(p,0xCB);                          // mov ecx,ebx
    p=EB(p,0x83);p=EB(p,0xE1);p=EB(p,0x0F);               // and ecx,15 (c)
    p=EB(p,0xC1);p=EB(p,0xEB);p=EB(p,0x04);               // shr ebx,4 (r)
    p=EB(p,0x33);p=EB(p,0xD2);                          // xor edx,edx
    p=EB(p,0x8B);p=EB(p,0xC7);                          // mov eax,edi (page)
    p=EB(p,0xBF);p=EI(p,GRID_COLS);                       // mov edi,5
    p=EB(p,0xF7);p=EB(p,0xF7);                          // div edi -> eax=gpr, edx=gpc
    p=EB(p,0xC1);p=EB(p,0xE2);p=EB(p,0x04);               // shl edx,4
    p=EB(p,0x03);p=EB(p,0xD1);                          // add edx,ecx (COL)
    p=EB(p,0x6B);p=EB(p,0xC0);p=EB(p,12);                 // imul eax,eax,12
    p=EB(p,0x03);p=EB(p,0xC3);                          // add eax,ebx (ROW)
    // log (COL=edx, ROW=eax) into g_bk ring
    p=EB(p,0x50);
    p=EB(p,0x52);
    p=EB(p,0xA1);p=EI(p,(unsigned int)g_ik);
    p=EB(p,0x89);p=EB(p,0x14);p=EB(p,0xC5);p=EI(p,(unsigned int)g_bk);
    p=EB(p,0x8B);p=EB(p,0x54);p=EB(p,0x24);p=EB(p,0x04);
    p=EB(p,0x89);p=EB(p,0x14);p=EB(p,0xC5);p=EI(p,(unsigned int)g_bk+4);
    p=EB(p,0x83);p=EB(p,0xC0);p=EB(p,0x01);
    p=EB(p,0x25);p=EI(p,MASK);
    p=EB(p,0xA3);p=EI(p,(unsigned int)g_ik);
    p=EB(p,0x5A);
    p=EB(p,0x58);
    p=EB(p,0x89);p=EB(p,0x55);p=EB(p,0xFC);               // mov [ebp-4],edx
    p=EB(p,0xDB);p=EB(p,0x45);p=EB(p,0xFC);               // fild dword [ebp-4]
    p=EB(p,0xDC);p=EB(p,0x0D);p=EI(p,0x882A30);           // fmul qword [0x882a30]
    p=EB(p,0xD9);p=EB(p,0x1E);                          // fstp dword [esi]
    p=EB(p,0x89);p=EB(p,0x45);p=EB(p,0xFC);               // mov [ebp-4],eax
    p=EB(p,0xDB);p=EB(p,0x45);p=EB(p,0xFC);               // fild dword [ebp-4]
    p=EB(p,0xDC);p=EB(p,0x0D);p=EI(p,0x882A30);           // fmul qword [0x882a30]
    p=EB(p,0xD9);p=EB(p,0x5E);p=EB(p,0x04);               // fstp dword [esi+4]
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,0xB18F9C);           // mov edx,[0xb18f9c]
    p=EB(p,0xC7);p=EB(p,0x46);p=EB(p,0x08);p=EI(p,0);       // mov dword [esi+8],0
    p=EB(p,0x89);p=EB(p,0x56);p=EB(p,0x0C);               // mov [esi+0xc],edx
    p=EB(p,0x8B);p=EB(p,0xC6);                          // mov eax,esi
    p=EB(p,0x5F);p=EB(p,0x5B);p=EB(p,0x5E);             // pop edi;pop ebx;pop esi
    p=EB(p,0x8B);p=EB(p,0xE5);p=EB(p,0x5D);p=EB(p,0xC3); // mov esp,ebp;pop ebp;ret
    Lorig=p; fixj32(j1,Lorig); fixj32(j2,Lorig);
    p=EB(p,0x55);p=EB(p,0x8B);p=EB(p,0xEC);p=EB(p,0x51);p=EB(p,0x56);
    p=EJMP(p, base+0x178685);
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
    unsigned int ss=256, bs=RING*sizeof(ENT);
    unsigned int nstub=1+1+1+5+N_LS;
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
