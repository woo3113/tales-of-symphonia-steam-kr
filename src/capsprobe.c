#include <stdio.h>
#include <d3d9.h>
int main(void){
    IDirect3D9* d3d = Direct3DCreate9(D3D_SDK_VERSION);
    if(!d3d){ printf("Direct3DCreate9 failed\n"); return 1; }
    UINT n = d3d->lpVtbl->GetAdapterCount(d3d);
    printf("adapters=%u\n", n);
    for(UINT i=0;i<n;i++){
        D3DADAPTER_IDENTIFIER9 id;
        D3DCAPS9 caps;
        if(SUCCEEDED(d3d->lpVtbl->GetAdapterIdentifier(d3d,i,0,&id)))
            printf("adapter %u: %s\n", i, id.Description);
        if(SUCCEEDED(d3d->lpVtbl->GetDeviceCaps(d3d,i,D3DDEVTYPE_HAL,&caps)))
            printf("  MaxTextureWidth=%u MaxTextureHeight=%u\n", caps.MaxTextureWidth, caps.MaxTextureHeight);
        else
            printf("  GetDeviceCaps(HAL) failed\n");
    }
    d3d->lpVtbl->Release(d3d);
    return 0;
}
