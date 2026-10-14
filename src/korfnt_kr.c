// korfnt_kr (release = logger23 built with -DRELEASE: no main-loop tap, no krcodes.bin/voicelog.txt).
// logger23: logger22 + voice-language sync hook at 0x582840 (fixes in-game English voices with JP setting).
// logger22: logger21 + voice-language probe (voicelog.txt: lang flag + opened SCE AWBs over time).
// logger21: logger20 + field action label loop (0x4D77C0) maps glyph index -> byte offset for 2-byte codes.
// logger20: logger19 + length site 0x4F9619 (description/typewriter text was read 1 byte at a time).
// logger19: logger18 + length stubs replay skipped side-effect instructions on the 'ours' path
//           (fixes name plates @57682D byte-count, stack leak @4D7D6C, etc).
// logger18: logger17 + name-plate width fix (0x57AB37 ours->48), drop typo patch at 0x557BA5 (jump table!),
//           conv 0x538809 ours -> 0x538902 (preset width 48, no OOB table read).
// logger17: logger16 + preserve edx in len/conv/width stubs (OURSIDX clobbers edx).
// logger16: logger15 + fix: cmp/sub with imm>=0x80 used 83 /r imm8 (sign-extended) -> now 81 /r imm32.
// logger15: B-pipeline with EUC-KR *symbol* support (A1..AF rows) + verified ecx-safe length stubs.
//   - 26 length-rule sites: our codes (Hangul or symbol) read as 2 bytes
//   - 5 converter copies: EUC-KR Hangul -> 0x4000+(b0-0xB0)*94+(b1-0xA1)
//                         EUC-KR symbol lead A1..AF -> 0x4000+2445+(b0-0xA1)*94+(b1-0xA1)
//   - glyph slot 0x578680: ax in [0x4000,0x4000+3855) -> group=2+idx/192, slot=idx%192
//   - width 0x57ACD0: ours -> 48
#include <windows.h>
#include "lensites.h"

#define RING 4096
#define MASK (RING-1)
#define GBASE 0x4000
#define GCOUNT 3855
#define GPAGEOFF 2
#define SYMBASE 2445
#define MAXNOT 12
typedef struct { unsigned int a,b; } ENT;
static unsigned char* g_mem;
static unsigned int *g_i0, *g_ik;
static unsigned int *g_gi;          // glyph stub call counter (debug)
static ENT *g_b0, *g_bk, *g_gr;     // debug rings
static char g_out[MAX_PATH]={0};

static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EW(unsigned char*p,unsigned short v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);return p+2;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE9);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
static void fixj(unsigned char* op,unsigned char* tgt){*op=(unsigned char)(tgt-(op+1));}
static void fixj32(unsigned char* op,unsigned char* tgt){unsigned int n=(unsigned int)(tgt-(op+4));EI(op,n);}

// Classify 16-bit code in Rw. Ours (Hangul KS X 1001, or EUC-KR symbol lead A1..AF) ->
// eax = 0x4000 + idx (fall through). Otherwise jump to each recorded jnot[] slot. clobbers eax,ecx,edx.
static unsigned char* OURSIDX(unsigned char* p,unsigned char R,unsigned char** jnot,int* m){
    int n=0;
    unsigned char *js1,*js2,*jd;
    #define JNOT(cc) do{ p=EB(p,0x0F); p=EB(p,0x80|(cc)); jnot[n++]=p; p=EI(p,0);}while(0)
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);        // movzx eax,Rw
    p=EB(p,0x8B);p=EB(p,0xD0);                        // mov edx,eax
    p=EB(p,0xC1);p=EB(p,0xEA);p=EB(p,0x08);             // shr edx,8   (lead)
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0xC8);           // movzx ecx,al (trail)
    p=EB(p,0x81);p=EB(p,0xFA);p=EI(p,0xB0);             // cmp edx,0xB0
    p=EB(p,0x72); js1=p; p=EB(p,0x00);                // jb SYM
    p=EB(p,0x81);p=EB(p,0xFA);p=EI(p,0xC8);             // cmp edx,0xC8
    p=EB(p,0x77); js2=p; p=EB(p,0x00);                // ja SYM
    // ---- HANGUL ----
    p=EB(p,0x81);p=EB(p,0xF9);p=EI(p,0xA1); JNOT(0x2);  // cmp ecx,0xA1; jb NOT
    p=EB(p,0x81);p=EB(p,0xF9);p=EI(p,0xFE); JNOT(0x7);  // cmp ecx,0xFE; ja NOT
    p=EB(p,0x81);p=EB(p,0xEA);p=EI(p,0xB0);             // sub edx,0xB0
    p=EB(p,0x6B);p=EB(p,0xD2);p=EB(p,94);               // imul edx,edx,94
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xA1);             // sub ecx,0xA1
    p=EB(p,0x03);p=EB(p,0xD1);                        // add edx,ecx
    p=EB(p,0x8D);p=EB(p,0x82);p=EI(p,0x4000);         // lea eax,[edx+0x4000]
    p=EB(p,0xE9); jd=p; p=EI(p,0);                    // jmp DONE
    // ---- SYMBOL ----
    unsigned char* Ls=p; fixj(js1,Ls); fixj(js2,Ls);
    p=EB(p,0x81);p=EB(p,0xFA);p=EI(p,0xA1); JNOT(0x2);  // cmp edx,0xA1; jb NOT
    p=EB(p,0x81);p=EB(p,0xFA);p=EI(p,0xAF); JNOT(0x7);  // cmp edx,0xAF; ja NOT
    p=EB(p,0x81);p=EB(p,0xF9);p=EI(p,0xA1); JNOT(0x2);  // cmp ecx,0xA1; jb NOT
    p=EB(p,0x81);p=EB(p,0xF9);p=EI(p,0xFE); JNOT(0x7);  // cmp ecx,0xFE; ja NOT
    p=EB(p,0x81);p=EB(p,0xEA);p=EI(p,0xA1);             // sub edx,0xA1
    p=EB(p,0x6B);p=EB(p,0xD2);p=EB(p,94);               // imul edx,edx,94
    p=EB(p,0x81);p=EB(p,0xE9);p=EI(p,0xA1);             // sub ecx,0xA1
    p=EB(p,0x03);p=EB(p,0xD1);                        // add edx,ecx
    p=EB(p,0x81);p=EB(p,0xC2);p=EI(p,SYMBASE);        // add edx,SYMBASE
    p=EB(p,0x8D);p=EB(p,0x82);p=EI(p,0x4000);         // lea eax,[edx+0x4000]
    // ---- DONE ----
    unsigned char* Ld=p; fixj32(jd,Ld);
    *m=n;
    #undef JNOT
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
static unsigned char* stub_len(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_len2,unsigned int r_resume,unsigned int base,unsigned int r_w48){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);p=EB(p,0x51);p=EB(p,0x52);         // push eax; push ecx; push edx (OURSIDX clobbers all 3)
    p=OURSIDX(p,R,jnot,&m);
    p=EB(p,0x5A);p=EB(p,0x59);p=EB(p,0x58);         // pop edx; pop ecx; pop eax
    // replay the original bytes between the patch and `cmp; ja` (mov R3,0xFE plus any side effects
    // such as `add esp,4` @4D7D6C, `mov [esp+0x28],2` @576832, `mov eax,esi` @5387B8). Must be
    // read before patch() overwrites the site. All of them are position independent.
    { unsigned char* o=(unsigned char*)(base+r_resume-5); unsigned char* e=(unsigned char*)(base+r_len2);
      e -= (e[-2]==0x77) ? 2 : 6;                   // ja rel8 / ja rel32
      e -= 3;                                       // cmp r16,r16 (66 3B xx)
      while(o<e) p=EB(p,*o++); }
    if(r_w48){ p=EB(p,0xB8);p=EI(p,0x30); p=EJMP(p, base+r_w48); }  // ours -> eax=48, skip width(al) call
    else p=EJMP(p, base+r_len2);                    // ours -> len2
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x5A);p=EB(p,0x59);p=EB(p,0x58);         // pop edx; pop ecx; pop eax
    p=EB(p,0xB8|R3); p=EI(p,0xFE);                  // mov R3,0xFE (replay)
    p=EJMP(p, base+r_resume);
    return p;
}
// 0x4F9619 (typewriter/description text, e.g. Custom menu help): `mov edi,0xFE; lea ecx,[esi+0x7EFF];
// cmp cx,di; mov edi,[ebp+0xC]; ja 1byte; inc edi; mov [ebp+0xC],edi; jmp 0x4F9634`. Code in esi.
static unsigned char* stub_len4f(unsigned char* p,unsigned int base){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);p=EB(p,0x51);p=EB(p,0x52);
    p=OURSIDX(p,6,jnot,&m);
    p=EB(p,0x5A);p=EB(p,0x59);p=EB(p,0x58);
    p=EB(p,0x8B);p=EB(p,0x7D);p=EB(p,0x0C);           // mov edi,[ebp+0xC]
    p=EB(p,0x47);                                     // inc edi
    p=EB(p,0x89);p=EB(p,0x7D);p=EB(p,0x0C);           // mov [ebp+0xC],edi
    p=EJMP(p, base+0xF9634);
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x5A);p=EB(p,0x59);p=EB(p,0x58);
    p=EB(p,0xBF);p=EI(p,0xFE);                        // mov edi,0xFE (replay)
    p=EJMP(p, base+0xF961E);
    return p;
}
// ---- field action label (e.g. K [대화한다]) draw loop 0x4D77C0..0x4D7968 ----
// The loop indexes the string by glyph number (edi) as if 1 glyph = 1 byte. Map glyph -> byte offset.
static int is2(const unsigned char* q){
    unsigned b0=q[0], b1=q[1];
    if(b1>=0xA1 && b1<=0xFE && ((b0>=0xB0&&b0<=0xC8)||(b0>=0xA1&&b0<=0xAF))) return 1;
    return 0;
}
static unsigned int __cdecl lbl_off(const unsigned char* s, unsigned int idx){
    unsigned int p=0;
    while(idx--){ if(!s[p]) break; p += is2(s+p) ? 2 : 1; }
    return p;
}
static unsigned int __cdecl lbl_code(const unsigned char* s, unsigned int idx){
    const unsigned char* q=s+lbl_off(s,idx);
    return is2(q) ? ((unsigned)q[0]<<8)|q[1] : q[0];
}
static unsigned char* ECALL(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE8);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
// replaces `movzx/movsx eax,byte [edi+esi]; call width` -> eax = width(code of glyph edi)
static unsigned char* stub_lblw(unsigned char* p,unsigned int base,unsigned int resume){
    p=EB(p,0x51);p=EB(p,0x52);                        // push ecx; push edx
    p=EB(p,0x57);p=EB(p,0x56);                        // push edi; push esi
    p=ECALL(p,(unsigned int)lbl_code);
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x08);           // add esp,8
    p=EB(p,0x5A);p=EB(p,0x59);                        // pop edx; pop ecx
    p=ECALL(p,base+0x17ACD0);                         // call width
    return EJMP(p,base+resume);
}
// replaces `movzx eax,byte [edi+esi]; movzx ecx,byte [edi+esi+1]` @4D78ED
static unsigned char* stub_lbladv(unsigned char* p,unsigned int base){
    p=EB(p,0x57);p=EB(p,0x56);                        // push edi; push esi
    p=ECALL(p,(unsigned int)lbl_off);                 // eax = byte offset
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0x4C);p=EB(p,0x06);p=EB(p,0x01); // movzx ecx,byte [esi+eax+1]
    p=EB(p,0x51);                                     // push ecx
    p=EB(p,0x8B);p=EB(p,0x44);p=EB(p,0x24);p=EB(p,0x08); // mov eax,[esp+8] (idx)
    p=EB(p,0x50);p=EB(p,0x56);                        // push eax; push esi
    p=ECALL(p,(unsigned int)lbl_code);                // eax = code (full for ours -> width 48 on 1-byte path)
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x08);           // add esp,8
    p=EB(p,0x59);                                     // pop ecx
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x08);           // add esp,8 (esi,edi)
    return EJMP(p,base+0xD78F6);
}
// Voice language sync. The game only copies the Voice Language setting (cfg+0x274, cfg=[0xAD3F68]) into the
// sound flag [0xB1864E] via 0x583020, which with our DLL loaded is not reached at boot -> event voices open
// from WIN/ (English). Hook the scene-AWB opener 0x582840 (main/sound thread) and sync before opening.
static unsigned char* stub_vsync(unsigned char* p,unsigned int base){
    unsigned char *jz,*je;
    p=EB(p,0x60);                                               // pushad
    p=EB(p,0xA1);p=EI(p,0xAD3F68);                              // mov eax,[0xAD3F68]
    p=EB(p,0x85);p=EB(p,0xC0);                                  // test eax,eax
    p=EB(p,0x74); jz=p; p=EB(p,0);                              // jz skip
    p=EB(p,0x0F);p=EB(p,0xBE);p=EB(p,0x80);p=EI(p,0x274);       // movsx eax,byte [eax+0x274]
    p=EB(p,0x85);p=EB(p,0xC0);                                  // test eax,eax
    p=EB(p,0x0F);p=EB(p,0x95);p=EB(p,0xC0);                     // setnz al
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0xC0);                     // movzx eax,al
    p=EB(p,0x3A);p=EB(p,0x05);p=EI(p,0xB1864E);                 // cmp al,[0xB1864E]
    p=EB(p,0x74); je=p; p=EB(p,0);                              // je skip
    p=EB(p,0x50);                                               // push eax
    p=ECALL(p,base+0x183020);                                   // call set_voice_lang
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);                     // add esp,4
    fixj(jz,p); fixj(je,p);
    p=EB(p,0x61);                                               // popad
    p=EB(p,0x55);p=EB(p,0x8B);p=EB(p,0xEC);                     // push ebp; mov ebp,esp (replay)
    p=EB(p,0x81);p=EB(p,0xEC);p=EI(p,0x104);                    // sub esp,0x104 (replay)
    return EJMP(p,base+0x182849);
}
static unsigned char* stub_conv(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_resume,unsigned int r_end,int is_ret,unsigned int base,unsigned int idxb,unsigned int buf){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    (void)idxb;(void)buf;
    p=EB(p,0x50);p=EB(p,0x52);                      // push eax; push edx
    p=OURSIDX(p,R,jnot,&m);
    p=EB(p,0x5A);                                   // pop edx
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);         // add esp,4
    if(is_ret){ p=EB(p,0xC3); } else { p=EJMP(p, base+r_end); }
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x5A);p=EB(p,0x58);                      // pop edx; pop eax
    p=EB(p,0xB8|R3); p=EI(p,0x80);                  // mov R3,0x80 (replay)
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_width(unsigned char* p,unsigned int base){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);p=EB(p,0x52);                      // push eax; push edx
    p=OURSIDX(p,0,jnot,&m);
    p=EB(p,0x5A);p=EB(p,0x58);                      // pop edx; pop eax
    p=EB(p,0xB8);p=EI(p,0x30);                      // mov eax,48
    p=EB(p,0xC3);                                   // ret
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x5A);p=EB(p,0x58);                      // pop edx; pop eax
    p=EB(p,0x8B);p=EB(p,0xC1);                      // mov ecx,eax (replay)
    p=EB(p,0x81);p=EB(p,0xE1);p=EI(p,0xFF00);       // and ecx,0xff00
    p=EJMP(p, base+0x17ACD8);
    return p;
}
static unsigned char* stub_glyph(unsigned char* p,unsigned int base){
    // debug: record every glyph call (code=ax, retaddr=[esp]) into g_gr ring
    p=EB(p,0x50);p=EB(p,0x51);p=EB(p,0x52);
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0);                // movzx eax,ax
    p=EB(p,0x8B);p=EB(p,0x54);p=EB(p,0x24);p=EB(p,0x0C);   // mov edx,[esp+0xC]
    p=EB(p,0x8B);p=EB(p,0x0D);p=EI(p,(unsigned int)g_gi);
    p=EB(p,0x89);p=EB(p,0x04);p=EB(p,0xCD);p=EI(p,(unsigned int)g_gr);
    p=EB(p,0x89);p=EB(p,0x14);p=EB(p,0xCD);p=EI(p,(unsigned int)g_gr+4);
    p=EB(p,0x83);p=EB(p,0xC1);p=EB(p,0x01);
    p=EB(p,0x81);p=EB(p,0xE1);p=EI(p,MASK);
    p=EB(p,0x89);p=EB(p,0x0D);p=EI(p,(unsigned int)g_gi);
    p=EB(p,0x5A);p=EB(p,0x59);p=EB(p,0x58);
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
    p=EB(p,0x52);p=EB(p,0x56);                          // push edx; push esi
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
    unsigned int i0=*g_i0, ik=*g_ik, ig=*g_gi;
    WriteFile(h,&i0,4,&w,0);WriteFile(h,&ik,4,&w,0);WriteFile(h,&ig,4,&w,0);
    WriteFile(h,g_b0,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_bk,sizeof(ENT)*RING,&w,0);
    WriteFile(h,g_gr,sizeof(ENT)*RING,&w,0);
    CloseHandle(h);
}
static DWORD WINAPI worker(LPVOID a){
    (void)a;
    Sleep(60);
    unsigned int base=(unsigned int)GetModuleHandleA(NULL);
    unsigned int ss=512, bs=RING*sizeof(ENT);
    unsigned int nstub=1+1+1+5+N_LS+1+3+1;
    unsigned int total=ss*nstub+32+bs*3+16;
    g_mem=(unsigned char*)VirtualAlloc(0,total,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    if(!g_mem)return 0;
    unsigned char* s0=g_mem;
    unsigned char* sglyph=g_mem+ss;
    unsigned char* swidth=g_mem+ss*2;
    unsigned char* sconv=g_mem+ss*3;
    g_i0=(unsigned int*)(g_mem+ss*nstub); g_ik=g_i0+1; g_gi=g_i0+2;
    g_b0=(ENT*)(g_mem+ss*nstub+32);
    g_bk=(ENT*)((unsigned char*)g_b0+bs);
    g_gr=(ENT*)((unsigned char*)g_bk+bs);
    *g_i0=0; *g_ik=0; *g_gi=0;
#ifndef RELEASE
    { unsigned char* p=stub_bytes(s0,(unsigned int)g_i0,(unsigned int)g_b0,
        (unsigned char[]){0xDD,0x05,0x30,0x2A,0x88,0x00},6, base+0x17A8B6); (void)p; patch(base+0x17A8B0, s0, 6); }
#endif
    { stub_glyph(sglyph, base); patch(base+0x178680, sglyph, 6); }
    { stub_width(swidth, base); patch(base+0x17ACD0, swidth, 8); }
    { stub_conv(sconv+0*ss, 0, 1, 0x17A821, 0, 1, base, 0, 0); patch(base+0x17A81C, sconv+0*ss, 5); }
    { stub_conv(sconv+1*ss, 6, 1, 0x17A995, 0x17A9E4, 0, base, 0, 0); patch(base+0x17A990, sconv+1*ss, 5); }
    { stub_conv(sconv+2*ss, 6, 1, 0x154E23, 0x154E72, 0, base, 0, 0); patch(base+0x154E1E, sconv+2*ss, 5); }
    /* removed: was patch(base+0x157BA5) = typo for 0x17ABA5; it overwrote switch table 0x557AB8 entries 59/60 */
    { stub_conv(sconv+4*ss, 0, 2, 0x13880E, 0x138902, 0, base, 0, 0); patch(base+0x138809, sconv+4*ss, 5); }
    for(int i=0;i<N_LS;i++){
        unsigned char* st=g_mem+ss*(8+i);
        // 0x57AB37 (scaled string-width fn 0x57AAE0, used by name plates): its 2-byte path calls width(al)
        // with only the trail byte -> half width for ours. Feed 48 directly into 0x57AB49 instead.
        stub_len(st, g_ls[i].R, g_ls[i].R3, g_ls[i].len2, g_ls[i].patch+5, base, g_ls[i].patch==0x17AB37 ? 0x17AB49 : 0);
        patch(base+g_ls[i].patch, st, 5);
    }
    { unsigned char* st=g_mem+ss*(8+N_LS); stub_len4f(st, base); patch(base+0xF9619, st, 5); }
    { unsigned char* st=g_mem+ss*(9+N_LS);  stub_lblw(st, base, 0xD77E9); patch(base+0xD77E0, st, 9); }
    { unsigned char* st=g_mem+ss*(10+N_LS); stub_lblw(st, base, 0xD7844); patch(base+0xD783A, st, 10); }
    { unsigned char* st=g_mem+ss*(11+N_LS); stub_lbladv(st, base); patch(base+0xD78ED, st, 9); }
    { unsigned char* st=g_mem+ss*(12+N_LS); stub_vsync(st, base); patch(base+0x182840, st, 9); }
    {
        char e[MAX_PATH];GetModuleFileNameA(NULL,e,MAX_PATH);
        char* l=e; for(char*q=e;*q;q++) if(*q=='\\'||*q=='/') l=q;
        int k=(int)(l-e); for(int i=0;i<k;i++)g_out[i]=e[i];
        const char* su="\\krcodes.bin"; for(int j=0;su[j];j++) g_out[k++]=su[j]; g_out[k]=0;
    }
#ifdef RELEASE
    return 0;
#endif
    // voice-language probe: [0xB1864E]=voice lang (0=EN,1=JP), [0xB1AE6C+i]=AWB i opened, [0xB1C058+4i]=handle
    {
        char vp[MAX_PATH]; int k=0; for(;g_out[k] && k<MAX_PATH-1;k++) vp[k]=g_out[k];
        while(k>0 && vp[k-1]!=0x5C) k--; { const char* su="voicelog.txt"; for(int j=0;su[j];j++) vp[k++]=su[j]; vp[k]=0; }
        HANDLE h=CreateFileA(vp,GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);
        char last[160]={0}; DWORD t0=GetTickCount(), tick=0;
        for(;;){
            Sleep(200);
            char line[160]; int n=0; DWORD t=(GetTickCount()-t0)/1000;
            unsigned char lang=*(volatile unsigned char*)0xB1864E;
            line[n++]='L'; line[n++]=(char)('0'+lang); { unsigned int c=*(volatile unsigned int*)0xAD3F68; line[n++]='C'; line[n++]= c ? (char)('0'+((*(volatile unsigned char*)(c+0x274))&7)) : '-'; } line[n++]=' ';
            for(int i=0;i<0x14;i++){ unsigned char o=*(volatile unsigned char*)(0xB1AE6C+i); line[n++]= o ? (char)('A'+i) : '.'; }
            line[n]=0;
            int same=1; for(int i=0;i<=n;i++) if(line[i]!=last[i]){same=0;break;}
            if(!same && h!=INVALID_HANDLE_VALUE){
                char out[200]; int m=0; DWORD tt=t; char num[12]; int q=0; do{num[q++]=(char)('0'+tt%10);tt/=10;}while(tt);
                while(q) out[m++]=num[--q]; out[m++]='s'; out[m++]=' ';
                for(int i=0;i<n;i++) out[m++]=line[i]; out[m++]='\r'; out[m++]='\n';
                DWORD w; WriteFile(h,out,m,&w,0); FlushFileBuffers(h);
                for(int i=0;i<=n;i++) last[i]=line[i];
            }
            if(++tick%6==0) dump();
        }
    }
}
BOOL WINAPI DllMain(HINSTANCE h,DWORD r,LPVOID x){
    if(r==DLL_PROCESS_ATTACH){DisableThreadLibraryCalls(h);CreateThread(0,0,worker,0,0,0);}
    (void)h;(void)x;return TRUE;
}
