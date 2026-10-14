// logger6b: correct emitters, preserve ecx/edx.
//  - tap 0x57A8B0 (main text loop head): log eax(text ptr) + u32[eax]
//  - tap 0x57ACD0 (width):               log eax(code) + ret
//  - tap 0x578680 (glyph slot):          log eax(code) + ecx(ctx)
//  - tap 0x57A810/0x57A81C (converter):  log eax(code) + ret
//  - patch 0x57A8DA length rule: 2 bytes iff code in [0x8101,0x81FF] OR [0xB0A1,0xC8FE]
#include <windows.h>
#define RING 4096
#define MASK (RING-1)
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_i0,*g_i1,*g_i2,*g_i3;
static ENT *g_b0,*g_b1,*g_b2,*g_b3;
static char g_out[MAX_PATH]={0};

static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){
    unsigned char* q=EB(p,0xE9);
    unsigned int next=(unsigned int)(q+4);
    return EI(q,(unsigned int)(tgt-next));
}
// preserve edx+ecx; log (eax, ret=[esp+8] since we pushed edx,ecx)
static unsigned char* stub_ret(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52);                                   // push edx
    p=EB(p,0x51);                                   // push ecx
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);          // mov edx,[idx]
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);      // mov [edx*8+buf],eax
    p=EB(p,0x8B);p=EB(p,0x4C);p=EB(p,0x24);p=EB(p,0x08);     // mov ecx,[esp+8]
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);    // mov [edx*8+buf+4],ecx
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);         // add edx,1
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);         // and edx,MASK
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);          // mov [idx],edx
    p=EB(p,0x59);                                   // pop ecx
    p=EB(p,0x5A);                                   // pop edx
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    p=EJMP(p,resume);
    return p;
}
// preserve edx+ecx; log (eax, ecx)
static unsigned char* stub_ecx(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52);                                   // push edx
    p=EB(p,0x51);                                   // push ecx
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);          // mov edx,[idx]
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);      // mov [edx*8+buf],eax
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);    // mov [edx*8+buf+4],ecx
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x59);
    p=EB(p,0x5A);
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    p=EJMP(p,resume);
    return p;
}
// preserve edx+ecx; log (eax, *(u32*)eax)
static unsigned char* stub_bytes(unsigned char* p,unsigned int idx,unsigned int buf,unsigned char const* rep,int replen,unsigned int resume){
    p=EB(p,0x52);
    p=EB(p,0x51);
    p=EB(p,0x8B);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xD5);p=EI(p,buf);
    p=EB(p,0x8B);p=EB(p,0x08);                      // mov ecx,[eax]
    p=EB(p,0x89);p=EB(p,0x0C);p=EB(p,0xD5);p=EI(p,buf+4);
    p=EB(p,0x83);p=EB(p,0xC2);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE2);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x15);p=EI(p,idx);
    p=EB(p,0x59);
    p=EB(p,0x5A);
    for(int i=0;i<replen;i++) p=EB(p,rep[i]);
    p=EJMP(p,resume);
    return p;
}
static unsigned char* stub_len(unsigned char* p,unsigned int r1,unsigned int r2){
    p=EB(p,0x8D);p=EB(p,0x86);p=EB(p,0xFF);p=EB(p,0x7E);p=EB(p,0x00);p=EB(p,0x00);
    p=EB(p,0xBA);p=EI(p,0xFE);
    p=EB(p,0x66);p=EB(p,0x3B);p=EB(p,0xC2);
    p=EB(p,0x76); unsigned char* j1=p; p=EB(p,0x00);
    p=EB(p,0x8B);p=EB(p,0xC6);
    p=EB(p,0x25);p=EI(p,0xFFFF);
    p=EB(p,0x2D);p=EI(p,0xB0A1);
    p=EB(p,0x3D);p=EI(p,0x185D);
    p=EB(p,0x76); unsigned char* j2=p; p=EB(p,0x00);
    p=EJMP(p,r1);
    unsigned char* L2=p;
    p=EJMP(p,r2);
    *j1=(unsigned char)(L2-(j1+1));
    *j2=(unsigned char)(L2-(j2+1));
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
    unsigned int i0=*g_i0,i1=*g_i1,i2=*g_i2,i3=*g_i3;
    WriteFile(h,&i0,4,&w,0);WriteFile(h,&i1,4,&w,0);WriteFile(h,&i2,4,&w,0);WriteFile(h,&i3,4,&w,0);
    WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b1,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_b2,sizeof(ENT)*RING,&w,0);WriteFile(h,g_b3,sizeof(ENT)*RING,&w,0);
    CloseHandle(h);
}
static DWORD WINAPI worker(LPVOID a){
    (void)a;
    Sleep(60);
    unsigned int base=(unsigned int)GetModuleHandleA(NULL);
    unsigned int ss=160, bs=RING*sizeof(ENT);
    unsigned int total=ss*8+16+bs*4;
    g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!g_mem)return 0;
    unsigned char* s0=g_mem,*s1=g_mem+ss,*s2=g_mem+ss*2,*s3=g_mem+ss*3,*s4=g_mem+ss*4;
    g_i0=(unsigned int*)(g_mem+ss*8); g_i1=g_i0+1; g_i2=g_i0+2; g_i3=g_i0+3;
    g_b0=(ENT*)(g_mem+ss*8+16);
    g_b1=(ENT*)((unsigned char*)g_b0+bs);
    g_b2=(ENT*)((unsigned char*)g_b1+bs);
    g_b3=(ENT*)((unsigned char*)g_b2+bs);
    *g_i0=*g_i1=*g_i2=*g_i3=0;
    { unsigned char* p=stub_bytes(s0,(unsigned int)g_i0,(unsigned int)g_b0,
        (unsigned char[]){0xDD,0x05,0x30,0x2A,0x88,0x00},6, base+0x17A8B6); (void)p; patch(base+0x17A8B0, s0, 6); }
    { unsigned char* p=stub_ret(s1,(unsigned int)g_i1,(unsigned int)g_b1,
        (unsigned char[]){0x8B,0xC1,0x81,0xE1,0x00,0xFF,0x00,0x00},8, base+0x17ACD8); (void)p; patch(base+0x17ACD0, s1, 8); }
    { unsigned char* p=stub_ecx(s2,(unsigned int)g_i2,(unsigned int)g_b2,
        (unsigned char[]){0x55,0x8B,0xEC,0x51,0x56},5, base+0x178685); (void)p; patch(base+0x178680, s2, 5); }
    { unsigned char* p=stub_ret(s3,(unsigned int)g_i3,(unsigned int)g_b3,
        (unsigned char[]){0xB9,0x80,0x00,0x00,0x00},5, base+0x17A821); (void)p; patch(base+0x17A81C, s3, 5); }
    { stub_len(s4, base+0x17A923, base+0x17A8EA); patch(base+0x17A8DA, s4, 6); }
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
