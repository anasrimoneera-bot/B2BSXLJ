(function(){
  if(new URLSearchParams(location.search).get('edit')!=='1') return;
  var bar=document.createElement('div'); bar.id='editbar'; bar.setAttribute('contenteditable','false');
  bar.innerHTML='<span class="eb-status">点击「编辑」后可直接修改文字</span>'+
                '<button class="eb-edit">编辑</button><button class="eb-save">下载本页</button>';
  document.body.appendChild(bar);
  var editing=false;
  bar.querySelector('.eb-edit').onclick=function(){
    editing=!editing;
    document.body.setAttribute('contenteditable', editing?'true':'false');
    bar.setAttribute('contenteditable','false'); bar.classList.toggle('on', editing);
    this.textContent=editing?'退出编辑':'编辑';
    bar.querySelector('.eb-status').textContent=editing?'直接点击文字修改，完成后点「下载本页」':'点击「编辑」后可直接修改文字';
  };
  bar.querySelector('.eb-save').onclick=function(){
    var clone=document.documentElement.cloneNode(true);
    var b=clone.querySelector('#editbar'); if(b) b.remove();
    var bd=clone.querySelector('body'); if(bd) bd.removeAttribute('contenteditable');
    var html='<!DOCTYPE html>\n'+clone.outerHTML;
    var blob=new Blob([html],{type:'text/html;charset=utf-8'});
    var a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download=(location.pathname.split('/').pop()||'index.html'); document.body.appendChild(a); a.click(); a.remove();
  };
})();
