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
    const table=figure.nextElementSibling.querySelector('table');
    const narrowRows=[...table.tBodies[0].rows].map(row=>[...row.cells].map(cell=>cell.textContent));
    const wideRows=JSON.parse(figure.querySelector('[data-map-coordinate-rows]').textContent);
    select.closest('label').hidden=false;
    figure.querySelector('[data-map-wide]').hidden=true;
    select.addEventListener('change',()=>{
      const option=select.selectedOptions[0];
      image.src=option.value;
      image.width=Number(option.dataset.width);image.height=Number(option.dataset.height);
      image.alt=option.dataset.alt;
      figure.querySelector('[data-map-open]').href=option.value;
      figure.querySelector('[data-map-size]').textContent=option.dataset.description;
      const body=document.createElement('tbody');
      for(const cells of option.dataset.wideCoordinates?wideRows:narrowRows){
        const row=body.insertRow();
        cells.forEach(value=>row.insertCell().textContent=value);
      }
      table.tBodies[0].replaceWith(body);
      table.caption.textContent=option.textContent+' setup coordinates';
      viewport.scrollTop=0;
    });
  }
});
