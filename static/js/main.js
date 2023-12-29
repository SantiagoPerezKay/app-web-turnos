const bnt_delete=document.querySelectorAll('.btn-delete')

if (bnt_delete) {
    const btn_array=Array.from(bnt_delete);
    btn_array.forEach((btn) => {
        btn.addEventListener('click',(e)=>{
            if (!confirm('estas seguro de eliminar este registro?')){
                e.preventDefault();
            }

        });
        
    });

}