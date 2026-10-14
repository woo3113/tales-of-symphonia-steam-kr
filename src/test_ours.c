// Dump the generated OURSIDX / stub bytes for static disassembly.
#include <stdio.h>
#include <stdlib.h>
static unsigned char* EB(unsigned char*p,unsigned char b){*p++=b;return p;}
static unsigned char* EI(unsigned char*p,unsigned int v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);return p+4;}
static unsigned char* EJMP(unsigned char*p,unsigned int tgt){unsigned char*q=EB(p,0xE9);unsigned int n=(unsigned int)(q+4);return EI(q,(unsigned int)(tgt-n));}
static void fixj(unsigned char* op,unsigned char* tgt){*op=(unsigned char)(tgt-(op+1));}
static void fixj32(unsigned char* op,unsigned char* tgt){unsigned int n=(unsigned int)(tgt-(op+4));EI(op,n);}
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
int main(int argc,char**argv){
    unsigned char buf[256]; unsigned char* jn[MAXNOT]; int m=0;
    unsigned char* end=OURSIDX(buf,(unsigned char)atoi(argv[1]),jn,&m);
    int n=(int)(end-buf);
    printf("len=%d m=%d\n",n,m);
    for(int i=0;i<n;i++) printf("%02X",buf[i]);
    printf("\n");
    return 0;
}
