"use strict";
document.querySelectorAll('.battle-map').forEach(figure=>{
  const image=figure.querySelector('img'), viewport=figure.querySelector('.battle-map-viewport');
  const zoom=figure.querySelector('[data-map-zoom]'), select=figure.querySelector('[data-map-size-select]');
  zoom.hidden=false;
  zoom.addEventListener('click',()=>{
    const enlarged=figure.classList.toggle('is-enlarged');
    zoom.setAttribute('aria-pressed',String(enlarged));
    zoom.textContent=enlarged?'Fit map':'Enlarge';
    viewport.scrollTop=0;
    viewport.scrollLeft=enlarged?(viewport.scrollWidth-viewport.clientWidth)/2:0;
    viewport.focus({preventScroll:true});
  });
  if(select){
    select.closest('label').hidden=false;
    figure.querySelector('[data-map-wide]').hidden=true;
    select.addEventListener('change',()=>{
      const option=select.selectedOptions[0];
      image.src=option.value;
      image.width=Number(option.dataset.width);image.height=Number(option.dataset.height);
      figure.style.setProperty('--map-width',option.dataset.width+'px');
      image.alt=option.dataset.alt;
      figure.querySelector('[data-map-open]').href=option.value;
      figure.querySelector('[data-map-size]').textContent=option.dataset.description;
      viewport.scrollTop=0;
    });
  }
});
