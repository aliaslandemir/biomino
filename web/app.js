(() => {
  'use strict';
  const {records: compactRecords, metadata, datasets} = JSON.parse(document.getElementById('snapshot').textContent);
  const records = compactRecords.map(r => ({...r, ...datasets[r.dataset_key]}));
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number = value => value.toLocaleString('en-GB');
  const groups = [...new Set(metadata.taxa.map(t => t.group))];
  const colors = Object.fromEntries(metadata.taxa.map(t => [t.group, t.color]));
  const groupCounts = Object.fromEntries(groups.map(group => [group, records.filter(r => r.group === group).length]));
  const params = new URLSearchParams(location.search);
  const savedGroups = params.has('groups') ? params.get('groups').split(',').filter(g => groups.includes(g)) : groups;
  const state = {q:params.get('q') || '', species:params.get('species') || '', groups:new Set(savedGroups), since:params.get('since') || '', precision:params.get('precision') || '', view:params.get('view') === 'grid' ? 'grid' : 'records'};
  let filtered = [], shown = 30, toastTimer;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const map = L.map('map', {zoomControl:false, preferCanvas:true, minZoom:3, maxZoom:18, zoomAnimation:!reducedMotion, fadeAnimation:!reducedMotion});
  L.control.zoom({position:'topright'}).addTo(map);
  L.control.scale({position:'bottomright', imperial:false}).addTo(map);
  const currentTiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
  });
  let tileErrors = 0;
  currentTiles.on('tileerror', () => { if (++tileErrors >= 3) $('tile-warning').hidden = false; });
  currentTiles.on('tileload', () => { tileErrors = 0; $('tile-warning').hidden = true; });
  $('map').classList.add('muted-tiles');
  currentTiles.addTo(map);
  map.fitBounds([[57.4,3.5],[71.3,31]], {padding:[24,24]});
  const cluster = L.markerClusterGroup({chunkedLoading:true, chunkInterval:50, chunkDelay:10, maxClusterRadius:43, disableClusteringAtZoom:11, animate:!reducedMotion, showCoverageOnHover:false,
    iconCreateFunction: group => {
      const count = group.getChildCount(), size = count > 99 ? 43 : count > 9 ? 36 : 30;
      return L.divIcon({html:`<span class="cluster-bubble">${number(count)}</span>`, className:'cluster-icon', iconSize:[size,size]});
    }
  });
  const grid = L.layerGroup();
  const markerById = new Map();
  const searchable = new Map(records.map(r => [r.id, [r.species,r.common_name,r.locality,r.dataset,r.recorded_by].join(' ').toLowerCase()]));
  const licenseName = r => r.license.includes('/by/') ? 'CC BY 4.0' : 'CC0 1.0';
  const dateText = r => r.date ? String(r.date).split('T')[0] : r.year || 'Not reported';
  const basisText = r => r.basis.toLowerCase().replaceAll('_', ' ');
  function popup(r) {
    const datasetURL = `https://www.gbif.org/dataset/${encodeURIComponent(r.dataset_key)}`;
    const issues = r.issues.length ? r.issues.map(x => x.toLowerCase().replaceAll('_',' ')).join('; ') : 'None reported';
    return `<div class="popup"><div class="popup-eyebrow">${escape(r.group)} · GBIF ${escape(r.id)}</div><h3>${escape(r.common_name)}</h3><div class="scientific">${escape(r.species)}</div><dl><dt>Locality</dt><dd>${escape(r.locality)}</dd><dt>Recorded</dt><dd>${escape(dateText(r))}</dd><dt>Record type</dt><dd>${escape(basisText(r))}</dd><dt>Coordinates</dt><dd>${r.lat.toFixed(4)}° N, ${r.lon.toFixed(4)}° E</dd><dt>Uncertainty</dt><dd>${r.uncertainty_m == null ? 'Not reported' : number(r.uncertainty_m)+' m'}</dd><dt>Recorder</dt><dd>${escape(r.recorded_by || 'Not reported')}</dd><dt>Dataset</dt><dd><a href="${datasetURL}" target="_blank" rel="noopener noreferrer">${escape(r.dataset)}</a></dd><dt>GBIF flags</dt><dd>${escape(issues)}</dd></dl><a class="source-link" href="${escape(r.source)}" target="_blank" rel="noopener noreferrer">View original occurrence ↗</a><div class="license-note"><a href="${escape(r.license)}" target="_blank" rel="noopener noreferrer">${licenseName(r)}</a> · ${escape(r.citation || r.dataset)}<br>Reported occurrence; identification is supplied by the source.</div></div>`;
  }
  for (const r of records) {
    const marker = L.marker([r.lat,r.lon], {title:`${r.common_name} — ${r.locality}`, icon:L.divIcon({className:'point-icon', html:`<span class="point-dot" style="--point-color:${colors[r.group]}"></span>`,iconSize:[12,12],iconAnchor:[6,6]})});
    marker.bindTooltip(`${escape(r.common_name)} · ${escape(r.locality)}`, {direction:'top',offset:[0,-5]});
    // Popup markup is constructed only when requested.
    marker.bindPopup(() => popup(r), {maxWidth:300,minWidth:225,maxHeight:340,autoPanPaddingTopLeft:[20,90],autoPanPaddingBottomRight:[20,35]});
    markerById.set(r.id, marker);
  }
  $('total-records').textContent = number(records.length);
  $('total-species').textContent = metadata.taxa.length;
  $('snapshot-date').textContent = $('about-date').textContent = metadata.retrieved;
  for (const taxon of metadata.taxa) {
    const option = document.createElement('option');
    option.value = taxon.name; option.textContent = `${taxon.common_name} · ${taxon.name}`;
    $('species').append(option);
  }
  $('group-filters').innerHTML = groups.map(group => `<label class="group-option"><input type="checkbox" value="${escape(group)}" ${state.groups.has(group) ? 'checked' : ''}><span class="swatch" style="background:${colors[group]}"></span><span>${escape(group)}</span><span class="count">${number(groupCounts[group])}</span></label>`).join('');
  $('search').value = state.q;
  for (const key of ['species','since','precision']) {
    $(key).value = state[key]; state[key] = $(key).value; // Discard invalid URL options.
  }
  function updateURL() {
    const url = new URL(location.href);
    url.search = '';
    for (const key of ['q','species','since','precision']) if (state[key]) url.searchParams.set(key,state[key]);
    if (state.groups.size !== groups.length) url.searchParams.set('groups',[...state.groups].join(','));
    if (state.view !== 'records') url.searchParams.set('view',state.view);
    try { history.replaceState(null,'',url); } catch (_) { /* Local-file browsers may restrict history. */ }
  }
  function updateViewport() {
    const count = filtered.filter(r => map.getBounds().contains([r.lat,r.lon])).length;
    $('visible-summary').textContent = `${number(count)} of ${number(filtered.length)} records in view`;
  }
  map.on('moveend',updateViewport);
  map.on('popupopen',()=>document.querySelector('.map-area').classList.add('popup-open'));
  map.on('popupclose',()=>document.querySelector('.map-area').classList.remove('popup-open'));
  function renderList() {
    $('results').innerHTML = filtered.length ? filtered.slice(0,shown).map(r => `<button class="record-row" data-id="${escape(r.id)}"><span class="swatch" style="background:${colors[r.group]}"></span><span><strong>${escape(r.common_name)}</strong><small>${escape(r.locality)}</small></span><span class="record-year">${r.year || 'Undated'}</span></button>`).join('') : '<p class="empty">No records match these filters. Try another species, a wider date range, or reset the filters.</p>';
    $('more-results').hidden = shown >= filtered.length;
    $('more-results').textContent = `Show more (${number(filtered.length - shown)} remaining)`;
  }
  function buildGrid() {
    grid.clearLayers();
    const cells = new Map();
    for (const r of filtered) {
      const lat = Math.floor(r.lat*2)/2, lon = Math.floor(r.lon*2)/2, key = `${lat},${lon}`;
      if (!cells.has(key)) cells.set(key,{lat,lon,rows:[]});
      cells.get(key).rows.push(r);
    }
    for (const {lat,lon,rows} of cells.values()) {
      const count = rows.length, color = count >= 20 ? '#16464e' : count >= 10 ? '#367d83' : count >= 5 ? '#70a6a5' : '#b0cebd';
      L.rectangle([[lat,lon],[lat+.5,lon+.5]],{color:'#fff',weight:1,fillColor:color,fillOpacity:.75}).bindTooltip(`${number(count)} snapshot records · ${new Set(rows.map(r=>r.species)).size} species`).bindPopup(`<div class="popup"><div class="popup-eyebrow">0.5° COORDINATE GRID</div><h3>${number(count)} records</h3><p>${lat}–${lat+.5}° N · ${lon}–${lon+.5}° E</p><p>${[...new Set(rows.map(r=>r.common_name))].map(escape).join(', ')}</p><p class="license-note">Counts reflect the filtered snapshot and survey effort. Cells are not equal in area.</p></div>`).addTo(grid);
    }
  }
  function renderView() {
    map.closePopup();
    const isGrid = state.view === 'grid';
    if (isGrid) { map.removeLayer(cluster); buildGrid(); grid.addTo(map); }
    else { map.removeLayer(grid); cluster.addTo(map); }
    for (const mode of ['records','grid']) { $(`view-${mode}`).classList.toggle('active',state.view === mode); $(`view-${mode}`).setAttribute('aria-pressed',String(state.view === mode)); }
    $('legend-mode').textContent = isGrid ? '0.5° GRID' : 'OBSERVATIONS';
    $('legend').innerHTML = isGrid ? [['#b0cebd','1–4'],['#70a6a5','5–9'],['#367d83','10–19'],['#16464e','20+']].map(([color,label]) => `<span class="legend-item"><span class="swatch" style="background:${color};border-radius:1px"></span>${label} records</span>`).join('') : groups.map(group => `<span class="legend-item"><span class="swatch" style="background:${colors[group]}"></span>${escape(group)}</span>`).join('');
    $('legend-note').textContent = isGrid ? 'Records per coordinate cell. Survey effort varies; cells differ in area.' : 'A record marks a reported occurrence, not abundance.';
  }
  function applyFilters() {
    const terms = state.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    filtered = records.filter(r => state.groups.has(r.group) && (!state.species || r.species === state.species) && (!state.since || (r.year != null && r.year >= Number(state.since))) && (!state.precision || (r.uncertainty_m != null && r.uncertainty_m <= Number(state.precision))) && terms.every(t => searchable.get(r.id).includes(t)));
    // Filters use synchronous bulk insertion to prevent stale chunk queues after rapid edits.
    cluster.options.chunkedLoading = false;
    cluster.clearLayers(); cluster.addLayers(filtered.map(r => markerById.get(r.id)));
    shown = 30; renderList(); renderView(); updateViewport(); updateURL();
    $('result-count').textContent = number(filtered.length);
    $('map-subtitle').textContent = `${number(filtered.length)} matching records · ${new Set(filtered.map(r=>r.species)).size} species · ${metadata.retrieved}`;
    $('export').disabled = $('fit').disabled = filtered.length === 0;
  }
  let searchTimer;
  $('search').addEventListener('input',() => { clearTimeout(searchTimer); searchTimer = setTimeout(() => {state.q = $('search').value; applyFilters();},150); });
  for (const key of ['species','since','precision']) $(key).addEventListener('change',() => {state[key] = $(key).value; applyFilters();});
  $('group-filters').addEventListener('change',() => {state.groups = new Set([...$('group-filters').querySelectorAll('input:checked')].map(i=>i.value)); applyFilters();});
  $('reset').addEventListener('click',() => {
    clearTimeout(searchTimer); state.q = ''; $('search').value = '';
    for (const key of ['species','since','precision']) {state[key]=''; $(key).value='';}
    state.groups = new Set(groups); $('group-filters').querySelectorAll('input').forEach(i=>i.checked=true); applyFilters();
  });
  for (const mode of ['records','grid']) $(`view-${mode}`).addEventListener('click',() => {state.view=mode; renderView(); updateURL();});
  $('fit').addEventListener('click',() => {if(filtered.length) map.fitBounds(L.latLngBounds(filtered.map(r=>[r.lat,r.lon])), {padding:[40,70],maxZoom:11});});
  $('basemap').addEventListener('change',() => $('map').classList.toggle('muted-tiles',$('basemap').value === 'light'));
  $('more-results').addEventListener('click',() => {shown += 30; renderList();});
  function closeSidebar() { $('sidebar').classList.remove('open'); $('mobile-filters').setAttribute('aria-expanded','false'); }
  $('results').addEventListener('click',event => {
    const button = event.target.closest('[data-id]'); if(!button) return;
    state.view='records'; renderView(); updateURL(); closeSidebar();
    const marker = markerById.get(button.dataset.id);
    cluster.zoomToShowLayer(marker,() => marker.openPopup());
  });
  $('mobile-filters').addEventListener('click',() => {const open = $('sidebar').classList.toggle('open'); $('mobile-filters').setAttribute('aria-expanded',String(open)); if(open) $('search').focus();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape' && $('sidebar').classList.contains('open')) {closeSidebar(); $('mobile-filters').focus();}});
  map.on('click',closeSidebar);
  const dialog = $('about');
  $('about-open').addEventListener('click',()=>dialog.showModal()); $('methods-open').addEventListener('click',()=>dialog.showModal());
  $('about-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',event=>{if(event.target===dialog && (event.clientX < dialog.getBoundingClientRect().left || event.clientX > dialog.getBoundingClientRect().right || event.clientY < dialog.getBoundingClientRect().top || event.clientY > dialog.getBoundingClientRect().bottom)) dialog.close();});
  function toast(message) {clearTimeout(toastTimer); $('toast').textContent=message; $('toast').hidden=false; toastTimer=setTimeout(()=>$('toast').hidden=true,3500);}
  $('share').addEventListener('click',async()=>{
    updateURL();
    try {await navigator.clipboard.writeText(location.href); toast('Map link copied.');}
    catch (_) {toast('Copy the address from your browser to share these filters.');}
  });
  $('export').addEventListener('click',()=>{
    const collection={type:'FeatureCollection',name:'BiomiNO filtered occurrences',snapshot:metadata.retrieved,description:'Spatially thinned GBIF sample, not abundance or a complete inventory. Preserve feature attribution and licenses.',features:filtered.map(r=>({type:'Feature',id:r.id,geometry:{type:'Point',coordinates:[r.lon,r.lat]},properties:Object.fromEntries(Object.entries(r).filter(([k])=>!['lat','lon'].includes(k)))}))};
    const url=URL.createObjectURL(new Blob([JSON.stringify(collection,null,2)],{type:'application/geo+json'}));
    const link=document.createElement('a'); link.href=url; link.download=`biomino-${metadata.retrieved}.geojson`; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
    toast(`Exported ${number(filtered.length)} records with source credits.`);
  });
  document.querySelector('.brand').addEventListener('click',event=>{event.preventDefault(); $('reset').click(); state.view='records'; renderView(); updateURL(); map.fitBounds([[57.4,3.5],[71.3,31]],{padding:[24,24]});});
  applyFilters();
})();
