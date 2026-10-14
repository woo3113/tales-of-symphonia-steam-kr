// Dump all generated stubs for static disassembly.
#include <stdio.h>
#include <stdlib.h>
static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EW(unsigned char*p,unsigned short v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);return p+2;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE9);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
static void fixj(unsigned char* op,unsigned char* tgt){*op=(unsigned char)(tgt-(op+1));}
static void fixj32(unsigned char* op,unsigned char* tgt){unsigned int n=(unsigned int)(tgt-(op+4));EI(op,n);}
#define GBASE 0x4000
#define GCOUNT 3855
#define GPAGEOFF 2
#define SYMBASE 2445
#define MAXNOT 12
static unsigned char* OURSIDX(unsigned char* p,unsigned char R,unsigned char** jnot,int* m){
    int n=0; unsigned char *js1,*js2,*jd;
    #define JNOT(cc) do{ p=EB(p,0x0F); p=EB(p,0x80|(cc)); jnot[n++]=p; p=EI(p,0);}while(0)
    p=EB(p,0x0F);p=EB(p,0xB7);p=EB(p,0xC0|R);
    p=EB(p,0x8B);p=EB(p,0xD0);
    p=EB(p,0xC1);p=EB(p,0xEA);p=EB(p,0x08);
    p=EB(p,0x0F);p=EB(p,0xB6);p=EB(p,0xC8);
    p=EB(p,0x83);p=EB(p,0xFA);p=EB(p,0xB0);
    p=EB(p,0x72); js1=p; p=EB(p,0x00);
    p=EB(p,0x83);p=EB(p,0xFA);p=EB(p,0xC8);
    p=EB(p,0x77); js2=p; p=EB(p,0x00);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0xA1); JNOT(0x2);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0xFE); JNOT(0x7);
    p=EB(p,0x83);p=EB(p,0xEA);p=EB(p,0xB0);
    p=EB(p,0x6B);p=EB(p,0xD2);p=EB(p,94);
    p=EB(p,0x83);p=EB(p,0xE9);p=EB(p,0xA1);
    p=EB(p,0x03);p=EB(p,0xD1);
    p=EB(p,0x8D);p=EB(p,0x82);p=EI(p,0x4000);
    p=EB(p,0xE9); jd=p; p=EI(p,0);
    unsigned char* Ls=p; fixj(js1,Ls); fixj(js2,Ls);
    p=EB(p,0x83);p=EB(p,0xFA);p=EB(p,0xA1); JNOT(0x2);
    p=EB(p,0x83);p=EB(p,0xFA);p=EB(p,0xAF); JNOT(0x7);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0xA1); JNOT(0x2);
    p=EB(p,0x83);p=EB(p,0xF9);p=EB(p,0xFE); JNOT(0x7);
    p=EB(p,0x83);p=EB(p,0xEA);p=EB(p,0xA1);
    p=EB(p,0x6B);p=EB(p,0xD2);p=EB(p,94);
    p=EB(p,0x83);p=EB(p,0xE9);p=EB(p,0xA1);
    p=EB(p,0x03);p=EB(p,0xD1);
    p=EB(p,0x81);p=EB(p,0xC2);p=EI(p,SYMBASE);
    p=EB(p,0x8D);p=EB(p,0x82);p=EI(p,0x4000);
    unsigned char* Ld=p; fixj32(jd,Ld);
    *m=n; return p;
    #undef JNOT
}
static unsigned char* stub_len(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_len2,unsigned int r_resume,unsigned int base){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);p=EB(p,0x51);
    p=OURSIDX(p,R,jnot,&m);
    p=EB(p,0x59);p=EB(p,0x58);
    p=EJMP(p, base+r_len2);
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x59);p=EB(p,0x58);
    p=EB(p,0xB8|R3); p=EI(p,0xFE);
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_conv(unsigned char* p,unsigned char R,unsigned char R3,unsigned int r_resume,unsigned int r_end,int is_ret,unsigned int base){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);
    p=OURSIDX(p,R,jnot,&m);
    p=EB(p,0x83);p=EB(p,0xC4);p=EB(p,0x04);
    if(is_ret){ p=EB(p,0xC3); } else { p=EJMP(p, base+r_end); }
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x58);
    p=EB(p,0xB8|R3); p=EI(p,0x80);
    p=EJMP(p, base+r_resume);
    return p;
}
static unsigned char* stub_width(unsigned char* p,unsigned int base){
    unsigned char *jnot[MAXNOT],*Lorig; int m=0,i;
    p=EB(p,0x50);
    p=OURSIDX(p,0,jnot,&m);
    p=EB(p,0x58);
    p=EB(p,0xB8);p=EI(p,0x30);
    p=EB(p,0xC3);
    Lorig=p; for(i=0;i<m;i++) fixj32(jnot[i],Lorig);
    p=EB(p,0x58);
    p=EB(p,0x8B);p=EB(p,0xC1);
    p=EB(p,0x81);p=EB(p,0xE1);p=EI(p,0xFF00);
    p=EJMP(p, base+0x17ACD8);
    return p;
}
static void dump(const char*name,unsigned char*st,unsigned char*end){
    printf("%s len=%d\n",name,(int)(end-st));
    for(unsigned char*q=st;q<end;q++) printf("%02X",*q);
    printf("\n");
}
int main(){
    unsigned char b[512],*e;
    unsigned int base=0x400000;
    e=stub_len(b,6,1,0x17A923,0x17A8E5,base); dump("LEN_r6",b,e);
    e=stub_conv(b,6,1,0x17A995,0x17A9E4,0,base); dump("CONV_r6",b,e);
    e=stub_conv(b,0,1,0x17A821,0,1,base); dump("CONV_ret_r0",b,e);
    e=stub_width(b,base); dump("WIDTH",b,e);
    return 0;
}
