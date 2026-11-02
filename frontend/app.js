/* SPHEREx Motion Explorer. Original, dependency-light client, no fabricated science data. */
'use strict';
const $ = (id) => document.getElementById(id);
const CATALOG = {
  barnard:{name:"Barnard's Star",ra:269.452076958619,dec:4.693364966577,pmra:-801.551,pmdec:10362.394,epoch:2000,fov:9},
  epsilon:{name:'ε Indi B',ra:331.044146588521,dec:-56.782844195116,pmra:null,pmdec:null,epoch:2000,fov:10},
  wise0855:{name:'WISE 0855−0714',ra:133.818908333333,dec:-7.247047222222,pmra:-8124,pmdec:673,epoch:2000,fov:8},
  'rw-aur':{name:'RW Aurigae',ra:76.956526034583,dec:30.401438173889,pmra:7.23,pmdec:-20.33,epoch:2000,fov:8},
  'r-dra':{name:'R Draconis',ra:248.16761083295,dec:66.75497941722,pmra:0,pmdec:0,epoch:2000,fov:8},
};
let state = {
  observations:[], a:null, b:null, mode:'blink', playing:false,
  current:'a', clock:null, release:'qr3', allResults:[],
  images:{}, imageMetadata:null, renderKey:null, renderCounter:0,
  atlas:null, atlasInitializing:false, tab:'frames', queryCounter:0,
  sequence:[], sequenceImages:[], sequenceMetadata:null, sequenceKey:null,
  sequenceIndex:0, pendingView:null, coverage:null,
  spectrum:null, spectrumBusy:false, spectrumCounter:0,
  catalog:null, catalogBusy:false, catalogVisible:false,
  zoom:1, panX:0, panY:0, atlasMinimized:false,
};
const DETECTOR_COLORS={D1:'#7fd4ff',D2:'#8affc1',D3:'#ffe066',D4:'#ffab70',D5:'#ff8fa3',D6:'#c9a6ff',Unknown:'#9aa7b5'};
function el(tag,klass,text){const n=document.createElement(tag);if(klass)n.className=klass;if(text!==undefined)n.textContent=text;return n;}
function fmtDate(date){if(!date)return 'Date unspecified';const d=new Date(date);return Number.isNaN(+d)?date:d.toISOString().slice(0,10);}
function fmtWave(o){if(!o||o.wavelength_min_um==null||o.wavelength_max_um==null)return 'Not supplied';return `${o.wavelength_min_um.toFixed(3)}–${o.wavelength_max_um.toFixed(3)} µm`;}
// Metadata-only visualizations. No invented light curves, spectra, SNR or mock observations.
function drawTimeline(){
  const track=$('timelineTrack');if(!track)return;
  track.replaceChildren();
  const entries=state.observations.filter(x=>x.date_utc && Number.isFinite(Date.parse(x.date_utc)));
  $('timelineSummary').textContent=entries.length?`${entries.length} dated records · choose a marker to assign A/B`:'Search the archive to populate actual observation dates';
  $('timelineStart').textContent='—';$('timelineEnd').textContent='—';
  if(!entries.length){
    const empty=el('div','timeline-placeholder');
    empty.textContent='NO OBSERVATIONS LOADED · Timeline requires real archive timestamps';
    track.append(empty);return;
  }
  const ordered=[...entries].sort((a,b)=>Date.parse(a.date_utc)-Date.parse(b.date_utc));
  const min=Date.parse(ordered[0].date_utc),max=Date.parse(ordered.at(-1).date_utc);
  $('timelineStart').textContent=fmtDate(ordered[0].date_utc);
  $('timelineEnd').textContent=fmtDate(ordered.at(-1).date_utc);
  $('timelineMiddle').textContent='CLICK MARKER TO ASSIGN FRAME A / B';
  const daily=new Map();for(const ob of ordered){const key=fmtDate(ob.date_utc);if(!daily.has(key))daily.set(key,ob);}
  const all=[...daily.values()];const selected=[state.a,state.b,...state.sequence].filter(Boolean);
  // Keep the timeline operable with hundreds of real exposures. Prefer the selected observations.
  let chosen=all;
  if(chosen.length>65){const step=(chosen.length-1)/64;chosen=Array.from({length:65},(_,i)=>chosen[Math.round(step*i)]);}
  // Always include an explicitly selected exposure, even if not the daily representative.
  for(const ob of selected)if(!chosen.some(x=>x.id===ob.id))chosen.push(ob);
  for(const ob of chosen){
    const t=Date.parse(ob.date_utc),pos=max===min?50:2+96*(t-min)/(max-min);
    const btn=el('button','timeline-mark');btn.style.left=pos+'%';
    const isA=state.a?.id===ob.id,isB=state.b?.id===ob.id,isSequence=state.sequence.some(x=>x.id===ob.id);
    btn.classList.toggle('selected-a',isA);btn.classList.toggle('selected-b',isB);
    btn.classList.toggle('selected-sequence',!isA&&!isB&&isSequence);
    btn.title=`${fmtDate(ob.date_utc)} · ${ob.band} · click to ${state.a?'assign frame B':'assign frame A'}`;
    btn.setAttribute('aria-label',`Observation ${fmtDate(ob.date_utc)} detector ${ob.band}. Select as comparison frame`);
    btn.addEventListener('click',()=>selectFrame(state.a&&state.a.id!==ob.id?'b':'a',ob));
    track.append(btn);
  }
}
function updateSciencePanels(){
  const a=state.a,b=state.b;
  const seconds=a&&b?Math.abs(Date.parse(b.date_utc)-Date.parse(a.date_utc))/1000:NaN;
  $('baselineValue').textContent=Number.isFinite(seconds)?(seconds/86400).toFixed(2)+' days':'—';
  const plot=$('wavelengthPlot');plot.replaceChildren();
  let count=0;
  for(const [id,ob] of [['A',a],['B',b]]){
    if(!ob||!Number.isFinite(ob.wavelength_min_um)||!Number.isFinite(ob.wavelength_max_um))continue;
    count++;
    const row=el('div','wavelength-row');row.append(el('strong','',id));
    const track=el('div','wavelength-track'),range=el('div','wavelength-range '+id.toLowerCase());
    const clamp=v=>Math.max(0,Math.min(100,v));
    const start=clamp((ob.wavelength_min_um-0.75)/(5.0-0.75)*100);
    const end=clamp((ob.wavelength_max_um-0.75)/(5.0-0.75)*100);
    range.style.left=start+'%';range.style.width=Math.max(0,end-start)+'%';
    track.append(range);row.append(track,el('span','',ob.band+' · µm'));plot.append(row);
  }
  if(count){const axis=el('div','wave-axis');axis.append(el('span','','0.75 µm'),el('span','','3.0 µm'),el('span','','5.0 µm'));plot.append(axis);}
  else plot.append(el('div','wavelength-empty','Select observations to compare their reported wavelength coverage.'));
  const hasDates=Number.isFinite(seconds)&&seconds>0;
  $('dateCheck').textContent=hasDates?'✓':(a&&b?'!':'–');
  $('dateCheck').className='check-indicator'+(hasDates?' ok':a&&b?' warn':'');
  $('dateCheckText').textContent=hasDates?`Different epochs · ${(seconds/86400).toFixed(2)} days apart`:a&&b?'Same observation timestamp; motion baseline may be insufficient':'Choose exposures at different epochs';
  const sameBand=!!(a&&b&&a.band===b.band);
  $('bandCheck').textContent=sameBand?'✓':a&&b?'!':'–';
  $('bandCheck').className='check-indicator'+(sameBand?' ok':a&&b?' warn':'');
  $('bandCheckText').textContent=sameBand?`Same detector range (${a.band}); wavelength and PSF not guaranteed identical`:a&&b?`Different detector ranges (${a.band} vs ${b.band}); avoid brightness comparison`:'Match detector ranges before differencing';
}
function updateReviewCues(){
  const list=$('reviewCueList');if(!list)return;list.replaceChildren();
  const regions=state.imageMetadata?.exploratory_residual_regions||[];
  if(!regions.length){list.append(el('div','wavelength-empty',state.imageMetadata?'No strong residual regions in the current percentile cue.':'Select two frames and render B − A to inspect strong residual regions.'));return;}
  regions.slice(0,4).forEach((r,i)=>{const row=el('div','review-cue');row.append(el('span','',`Cue ${i+1} · ${r.pixels} px`),el('span','',`${r.sign} · (${r.x_pixel}, ${r.y_pixel})`));list.append(row);});
}
function coord(){return {ra:Number($('raInput').value),dec:Number($('decInput').value),fov:Number($('fovInput').value)};}
function validate(){const {ra,dec,fov}=coord();if(!Number.isFinite(ra)||ra<0||ra>=360||!Number.isFinite(dec)||dec<-90||dec>90||!Number.isFinite(fov)||fov<1||fov>18)throw Error('Coordinates must be valid decimal degrees (0 ≤ RA < 360, −90 ≤ Dec ≤ 90).');}
function setQueryStatus(text,error=false){$('queryStatus').textContent=text;$('queryStatus').classList.toggle('error',!!error);}
function updateCoverageSummary(){
  const box=$('coverageSummary'), text=$('coverageText');
  if(!box||!text)return;
  const c=state.coverage;
  if(!c||!c.dated_records){box.hidden=true;return;}
  box.hidden=false;
  const baseline=c.baseline_days!=null?`${c.baseline_days.toFixed(1)} d`:'not available';
  text.textContent=`${c.dated_records} dated archive records · ${fmtDate(c.earliest_utc)} → ${fmtDate(c.latest_utc)} · baseline ${baseline}`;
  $('baselineButton').disabled=state.allResults.filter(o=>o.date_utc).length<2;
}
function chooseWidestBaseline(){
  // SPHEREx frames span ~3.5 deg, so SIA 'intersections' often clip the field.
  // Prefer frames where the target sits well inside the detector so the local
  // spectral wavelength is measurable and the target is centred.
  const INTERIOR=90;
  const interior=x=>x.center_offset_arcmin==null||x.center_offset_arcmin<=INTERIOR;
  const byBand=new Map();
  for(const ob of state.allResults.filter(x=>x.date_utc)){
    const group=byBand.get(ob.band)||[];group.push(ob);byBand.set(ob.band,group);
  }
  let best=null;
  for(const [band,itemsAll] of byBand){
    for(const pool of [itemsAll.filter(interior),itemsAll]){
      items: {
        const items=pool;
        if(items.length<2)break items;
        items.sort((a,b)=>Date.parse(a.date_utc)-Date.parse(b.date_utc));
        const candidate={a:items[0],b:items[items.length-1],days:(Date.parse(items.at(-1).date_utc)-Date.parse(items[0].date_utc))/86400000,band,interior:pool!==itemsAll};
        if(!best||candidate.days>best.days)best=candidate;
        break items;
      }
      if(best)break; // interior pool found for this band; don't fall back
    }
  }
  if(!best){setQueryStatus('No two dated exposures share a detector range in this response. Try QR2, Deep fields, or a wider UTC range.',true);return;}
  state.a=best.a;state.b=best.b;stop();drawObservations();updateInspector();updateTransport();
  const tag=best.interior?'target-centred frames':'';
  setQueryStatus(`Selected widest same-detector baseline: ${best.days.toFixed(1)} days (${best.band})${tag}. Visual comparison remains exploratory.`);
  renderImages();
}
function approximatePosition(p){
  const year=new Date().getUTCFullYear()+(new Date().getUTCMonth()+0.5)/12;
  if(p.pmra===null||p.pmdec===null)return {ra:p.ra,dec:p.dec,estimated:false,year};
  // FIRST-ORDER proper motion only. pmRA is mu_alpha*cos(dec), not plain dRA/dt.
  const years=year-p.epoch;
  const ra=(p.ra+p.pmra*years/(3.6e6*Math.cos(p.dec*Math.PI/180))+360)%360;
  const dec=p.dec+p.pmdec*years/3.6e6;
  return {ra,dec,estimated:Math.abs(p.pmra)+Math.abs(p.pmdec)>300,year};
}
function setTarget(id){
  const p=CATALOG[id];if(!p)return;
  const position=approximatePosition(p);
  $('raInput').value=position.ra.toFixed(7);$('decInput').value=position.dec.toFixed(7);
  $('fovInput').value=p.fov;$('fovValue').textContent=p.fov+' arcmin';
  $('epochNote').textContent=position.estimated
    ? `Approx. ${position.year.toFixed(1)} centre from catalogue J2000 + proper motion; parallax and orbital motion not modelled.`
    : id==='epsilon' ? 'Catalog J2000 coordinate for ε Indi B. Proper motion of the binary is not applied; use a larger field.'
    : 'Catalogue J2000 coordinate; observational coordinates may vary with epoch.';
  $('fieldName').textContent=p.name;updateCoords();
}
function updateCoords(){
  const {ra,dec,fov}=coord();
  $('fieldCoords').textContent=`ICRS  ${ra.toFixed(6)}°  ${dec>=0?'+':''}${dec.toFixed(6)}°`;
  $('metaRa').textContent=ra.toFixed(7)+'°';$('metaDec').textContent=(dec>=0?'+':'')+dec.toFixed(7)+'°';
  $('metaFov').textContent=`${fov}′ × ${fov}′`;
  if($('viewportResolution'))$('viewportResolution').textContent=`FOV ${fov}′ × ${fov}′`;
  return {ra,dec,fov};
}
function stop(){if(state.clock!==null){clearInterval(state.clock);state.clock=null;}state.playing=false;$('playSymbol').textContent='▶';}
function resetPair(){stop();state.renderCounter++;state.a=null;state.b=null;
  state.sequence=[];state.sequenceImages=[];state.sequenceMetadata=null;state.sequenceKey=null;
  if(state.mode==='sequence'){
    state.mode='blink';document.querySelectorAll('.mode-button').forEach(b=>b.classList.toggle('active',b.dataset.mode==='blink'));
  }
  updateSequenceChips();state.renderKey=null;state.imageMetadata=null;clearImages();clearCatalogOverlay();$('gaiaToggle').disabled=true;
  $('imagePane').hidden=true;$('emptyStage').hidden=false;$('playBtn').disabled=true;$('downloadPng').disabled=true;updateInspector();updateTransport();}
function clearImages(){for(const url of Object.values(state.images)){if(url)URL.revokeObjectURL(url);}state.images={};}
async function search(){
  stop();const queryId=++state.queryCounter;
  try{
    validate();
    if($('startDate').value && $('endDate').value && $('startDate').value > $('endDate').value){
      throw Error('The UTC start date must be on or before the end date.');
    }
  }catch(error){setQueryStatus(error.message,true);return;}
  state.release=$('releaseSelect').value;const {ra,dec,fov}=coord();
  $('searchButton').disabled=true;setQueryStatus('Querying NASA/IPAC IRSA SIA v2…');
  resetPair();state.allResults=[];state.observations=[];drawObservations();
  const params=new URLSearchParams({ra:String(ra),dec:String(dec),fov:String(fov),release:state.release,survey:$('surveySelect').value});
  if($('startDate').value)params.set('start_date',$('startDate').value);
  if($('endDate').value)params.set('end_date',$('endDate').value);
  try{
    const response=await fetch('/api/observations?'+params,{headers:{Accept:'application/json'}});
    const payload=await response.json();if(!response.ok)throw Error(payload.detail||`Archive query failed (${response.status})`);
    if(queryId!==state.queryCounter)return;
    state.allResults=payload.observations;state.coverage=payload.coverage||null;filterObservations();updateCoverageSummary();
    if(state.pendingView){
      restoreViewSelection(state.pendingView);state.pendingView=null;
      await renderImages();
    }
    $('metaRelease').textContent=state.release.toUpperCase();
    const warning=payload.may_be_truncated?' Result cap reached; this may NOT include every epoch. Narrow the search in future releases.':'';
    setQueryStatus(`${state.allResults.length} IRSA FITS exposure records returned.${warning}`);
    if(!state.allResults.length){setQueryStatus('No compatible on-prem SPHEREx FITS images in this release. Try QR2, a different field, or check IRSA directly.');}
    const visibleParams=new URLSearchParams(params);
    visibleParams.set('band',$('bandSelect').value);
    history.replaceState({},'',`?${(state.a||state.sequence.length)?viewParams():visibleParams}`);
    if(state.tab==='atlas')updateAtlas();
  }catch(error){if(queryId===state.queryCounter){state.coverage=null;updateCoverageSummary();setQueryStatus(error.message,true);}}
  finally{if(queryId===state.queryCounter)$('searchButton').disabled=false;}
}
function filterObservations(){
  const band=$('bandSelect').value;
  state.observations=(band==='all'?state.allResults:state.allResults.filter(o=>o.band===band));
  drawObservations();
  setQueryStatus(`${state.observations.length} displayed · ${state.allResults.length} results in ${state.release.toUpperCase()}.`);
}
function drawObservations(){
  drawTimeline();
  const list=$('observationList');list.replaceChildren();
  $('resultCount').textContent=state.observations.length?String(state.observations.length):'—';
  if(!state.observations.length){list.append(el('div','list-placeholder',state.allResults.length?'No exposures in this detector range. Choose another.':'No observation records selected.'));return;}
  // Show a balanced sampling of early and late epochs while remaining responsive.
  let rows=state.observations;
  if(rows.length>96){const step=(rows.length-1)/95;rows=Array.from({length:96},(_,i)=>rows[Math.round(i*step)]);}
  for(const ob of rows){
    const row=el('div','obs-row');row.classList.toggle('selected',state.a?.id===ob.id||state.b?.id===ob.id||state.sequence.some(x=>x.id===ob.id));
    const detail=el('div');detail.append(el('div','obs-time',fmtDate(ob.date_utc)));
    const off=(ob.center_offset_arcmin!=null)?` · ${ob.center_offset_arcmin.toFixed(0)}′ off-axis`:'';
    detail.append(el('div','obs-desc',`${ob.band} · ${fmtWave(ob)}${off}`));
    const controls=el('div','obs-controls');
    for(const side of ['a','b']){
      const btn=el('button',state[side]?.id===ob.id?'active':'',side.toUpperCase());
      btn.title=`Use this exposure as frame ${side.toUpperCase()}`;
      btn.setAttribute('aria-label',`Select ${fmtDate(ob.date_utc)} ${ob.band} as frame ${side.toUpperCase()}`);
      btn.addEventListener('click',()=>selectFrame(side,ob));controls.append(btn);
    }
    const chosen=state.sequence.some(x=>x.id===ob.id);
    const seqButton=el('button',chosen?'sequence-active':'',chosen?'✓':'+');
    seqButton.title=chosen?'Remove from chronological sequence':'Add to chronological sequence (max 8)';
    seqButton.setAttribute('aria-label',(chosen?'Remove ':'Add ')+fmtDate(ob.date_utc)+' from sequence');
    seqButton.addEventListener('click',()=>toggleSequenceObservation(ob));controls.append(seqButton);
    row.append(detail,controls);list.append(row);
  }
  if(state.observations.length>rows.length)list.append(el('div','subnote',`Showing 96 of ${state.observations.length} records; the list samples the archive result chronologically.`));
}
function updateSequenceChips(){
  const rail=$('sequenceRail'), chips=$('sequenceChips');
  rail.hidden=state.sequence.length===0;
  $('sequenceCount').textContent=state.sequence.length+' / 8';
  const detectorSet=new Set(state.sequence.map(x=>x.band));
  $('sequenceRailCount').textContent=state.sequence.length+' FRAMES · '+(detectorSet.size>1?'MIXED DETECTORS':'CHRONOLOGICAL');
  $('clearSequence').disabled=!state.sequence.length;
  chips.replaceChildren();
  if(!state.sequence.length){chips.append(el('span','empty-tape','Select exposures using + in the archive list.'));return;}
  state.sequence.forEach((ob,i)=>{
    const chip=el('button','sequence-chip');
    chip.classList.toggle('active',state.mode==='sequence' && state.sequenceIndex===i);
    const localLam=state.sequenceMetadata?.frames?.[i]?.wavelength_local_um;
    chip.append(el('span','',`${i+1} / ${fmtDate(ob.date_utc)}`),
      el('small','',ob.band+' · '+(localLam!=null?localLam.toFixed(3)+' µm local':(ob.wavelength_min_um??'?')+' µm')));
    chip.title='Show this frame in the sequence';
    chip.addEventListener('click',()=>{
      state.sequenceIndex=i;
      if(state.mode==='sequence' && state.sequenceImages.length){stop();showRendered();}
      else if(state.sequence.length>=2)selectMode('sequence');
      updateSequenceChips();
    });chips.append(chip);
  });
}
function invalidateSequence(){
  stop();state.renderCounter++;state.sequenceKey=null;state.sequenceImages=[];state.sequenceMetadata=null;
  state.sequenceIndex=0;updateSequenceChips();updateInspector();updateTransport();
  if(state.mode==='sequence'){$('imagePane').hidden=true;$('emptyStage').hidden=false;}
}
function toggleSequenceObservation(ob){
  const index=state.sequence.findIndex(x=>x.id===ob.id);
  if(index>=0)state.sequence.splice(index,1);
  else{
    if(state.sequence.length===8){setQueryStatus('A time sequence is limited to eight observations for bounded memory and transfer costs.',true);return;}
    state.sequence.push(ob);
    if(new Set(state.sequence.map(x=>x.band)).size>1){
      setQueryStatus('Sequence mixes detector ranges. Position comparisons remain possible, but brightness changes are not comparable.',true);
    }
  }
  state.sequence.sort((a,b)=>(a.date_utc||'').localeCompare(b.date_utc||''));
  invalidateSequence();drawObservations();
  if(state.mode==='sequence'&&state.sequence.length>=2)renderImages();
}
function clearSequenceSelection(){
  state.sequence=[];invalidateSequence();drawObservations();
  if(state.mode==='sequence')selectMode('blink');
}
function restoreViewSelection(view){
  const find=id=>state.allResults.find(o=>o.id===id)||null;
  state.a=find(view.a_id);state.b=find(view.b_id);
  state.sequence=(view.sequence||'').split(',').filter(Boolean).slice(0,8).map(find).filter(Boolean);
  state.sequence.sort((a,b)=>(a.date_utc||'').localeCompare(b.date_utc||''));
  state.sequenceIndex=0;
  updateSequenceChips();drawObservations();updateInspector();updateTransport();
  if(['blink','split','mean','difference','sequence'].includes(view.mode)){
    state.mode=view.mode;
    if(state.mode==='sequence'&&state.sequence.length<2)state.mode='blink';
    document.querySelectorAll('.mode-button').forEach(b=>b.classList.toggle('active',b.dataset.mode===state.mode));
  }
  if((view.sequence && state.sequence.length<view.sequence.split(',').length) ||
     (view.a_id&&!state.a) || (view.b_id&&!state.b)){
    setQueryStatus('Some saved exposure IDs were absent from this archive search. Try widening the UTC range.',true);
  }
}
async function selectFrame(side,ob){
  if(state[side]?.id===ob.id)return;
  state[side]=ob;
  if(state.a&&state.b&&state.a.id===state.b.id){state[side==='a'?'b':'a']=null;}
  stop();drawObservations();updateInspector();updateTransport();await renderImages();
}
function updateInspector(){
  const a=state.a,b=state.b;
  document.querySelector('.inspector-lamp')?.classList.toggle('active',!!state.imageMetadata||!!state.sequenceMetadata);
  $('scienceState').textContent=state.mode==='sequence'&&state.sequence.length
    ? `${state.sequence.length} archive frames in chronological sequence`
    :a?(b?'Two archive frames selected':'One archive frame selected'):'No frame selected';
  $('exportEvidence').disabled=!(a||state.sequence.length);
  const display=(prefix,ob)=>{
    $('metaDate'+prefix).textContent=ob?fmtDate(ob.date_utc):'—';
    $('metaBand'+prefix).textContent=ob?ob.band:'—';
    $('metaWave'+prefix).textContent=ob?fmtWave(ob):'—';
    $('metaFlag'+prefix).textContent='—';
  };
  display('A',a);display('B',b);$('dateA').textContent=a?fmtDate(a.date_utc):'No observation';$('dateB').textContent=b?fmtDate(b.date_utc):'No observation';
  $('metaRelease').textContent=state.release.toUpperCase();
  updateSciencePanels();
  updateReviewCues();
  if(state.imageMetadata){
    for(const prefix of ['a','b']){
      const data=state.imageMetadata[prefix];if(data?.flagged_input_fraction!=null){
        $('metaFlag'+prefix.toUpperCase()).textContent=(100*data.flagged_input_fraction).toFixed(2)+'%';
      }
      const local=$('metaLocal'+prefix.toUpperCase());
      if(local){const lam=data?.wavelength_local_um;
        local.textContent=(lam!=null&&data?.bandwidth_local_um!=null)?`${lam.toFixed(3)} ± ${data.bandwidth_local_um.toFixed(3)} µm`:'unavailable';}
    }
    const match=state.imageMetadata.wavelength_match,lc=$('lambdaCheck'),lt=$('lambdaCheckText');
    if(match&&lc){lc.textContent=match.status==='matched'?'✓':match.status==='mismatched'?'!':'–';
      lc.className='check-indicator'+(match.status==='matched'?' ok':match.status==='mismatched'?' warn':'');
      lt.textContent=match.status==='matched'
        ?`Local wavelengths matched at target (Δλ ${match.delta_um.toFixed(3)} µm)`
        :match.status==='mismatched'
        ?`Local λ at target differs: A ${match.a_um?.toFixed(3)} vs B ${match.b_um?.toFixed(3)} µm (Δ ${match.delta_um?.toFixed(3)})`
        :'Local wavelength could not be determined for both frames';}
  } else {$('metaLocalA').textContent='—';$('metaLocalB').textContent='—';
    const lc=$('lambdaCheck');if(lc){lc.textContent='–';lc.className='check-indicator';}
    $('lambdaCheckText').textContent='Local wavelength match at target (from rendered metadata)';}
}
function updateTransport(){
  if(state.mode==='sequence'){
    $('playBtn').disabled=state.sequence.length<2 || state.sequenceImages.length<2;
    $('transportTitle').textContent=`${state.sequence.length} exposures · temporal playback`;
    $('transportSubtitle').textContent='Archive UTC order · one shared display brightness scale';
    return;
  }
  const a=state.a,b=state.b;$('playBtn').disabled=!(a&&b);
  $('transportTitle').textContent=!a?'Choose a pair of observations':!b?'Frame A selected · choose B':`${fmtDate(a.date_utc)}  /  ${fmtDate(b.date_utc)}`;
  $('transportSubtitle').textContent=a&&b
    ? (fmtDate(a.date_utc)===fmtDate(b.date_utc)?'Same UTC date; short time baseline limits visible motion.':'Playback compares aligned image frames')
    :'Two epochs are required for motion comparison.';
}
function renderURL(mode){
  const {ra,dec,fov}=coord();const qs=new URLSearchParams({ra:String(ra),dec:String(dec),fov:String(fov),a:state.a.token,mode});
  if(state.b)qs.set('b',state.b.token);
  return '/api/render?'+qs;
}
async function fetchRender(mode){
  const response=await fetch(renderURL(mode));
  if(!response.ok){let message=`Image processing failed: HTTP ${response.status}`;try{const o=await response.json();message=o.detail||message;}catch{}throw Error(message);}
  const md=response.headers.get('X-Science-Metadata');let meta=null;
  if(md){try{meta=JSON.parse(atob(md.replace(/-/g,'+').replace(/_/g,'/')));}catch{}}
  return {url:URL.createObjectURL(await response.blob()),meta};
}
async function renderImages(){
  stop();
  if(state.mode==='sequence'){await renderSequenceImages();return;}
  if(!state.a)return;
  const key=[state.a.id,state.b?.id||'',coord().ra,coord().dec,coord().fov].join('|');
  const newKey=state.renderKey!==key;
  if(newKey){clearImages();state.renderKey=key;state.imageMetadata=null;}
  const modes=state.b?['a','b']:['a'];
  if(state.mode==='difference')modes.push('difference');
  if(state.mode==='mean')modes.push('mean');
  const need=modes.filter(m=>!state.images[m]);
  if(!need.length){showRendered();return;}
  const renderId=++state.renderCounter;$('renderLoading').hidden=false;$('imageError').hidden=true;
  try{
    const loaded=await Promise.all(need.map(async m=>({mode:m,...await fetchRender(m)})));
    if(renderId!==state.renderCounter){loaded.forEach(v=>URL.revokeObjectURL(v.url));return;}
    for(const item of loaded){state.images[item.mode]=item.url;if(item.meta)state.imageMetadata=item.meta;}
    updateInspector();showRendered();
  }catch(error){if(renderId===state.renderCounter){$('imageError').textContent=error.message;$('imageError').hidden=false;$('emptyStage').hidden=false;$('imagePane').hidden=true;}}
  finally{if(renderId===state.renderCounter)$('renderLoading').hidden=true;}
}

async function renderSequenceImages(){
  if(state.sequence.length<2){setQueryStatus('Select at least two observations with + before opening Sequence.',true);return;}
  const c=coord();const key=[...state.sequence.map(o=>o.id),c.ra,c.dec,c.fov].join('|');
  if(key===state.sequenceKey&&state.sequenceImages.length===state.sequence.length){showRendered();return;}
  const renderId=++state.renderCounter;
  $('renderLoading').hidden=false;$('imageError').hidden=true;
  try{
    const response=await fetch('/api/sequence',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({ra:c.ra,dec:c.dec,fov:c.fov,tokens:state.sequence.map(o=>o.token)})
    });
    const payload=await response.json();
    if(!response.ok)throw Error(payload.detail||`Sequence processing failed: HTTP ${response.status}`);
    if(renderId!==state.renderCounter)return;
    state.sequenceImages=payload.images_base64.map(text=>'data:image/png;base64,'+text);
    state.sequenceMetadata=payload.metadata;state.sequenceKey=key;
    state.sequenceIndex=Math.min(state.sequenceIndex,state.sequenceImages.length-1);
    updateSequenceChips();updateInspector();showRendered();
  }catch(error){
    if(renderId===state.renderCounter){$('imageError').textContent=error.message;$('imageError').hidden=false;
      $('emptyStage').hidden=false;$('imagePane').hidden=true;}
  }finally{if(renderId===state.renderCounter){$('renderLoading').hidden=true;updateTransport();}}
}
function showRendered(){
  if(state.mode==='sequence'){
    if(state.sequenceImages.length<2)return;
    const i=state.sequenceIndex,ob=state.sequence[i],pane=$('imagePane');
    $('emptyStage').hidden=true;$('imageError').hidden=true;pane.hidden=false;pane.classList.remove('split');
    $('frameB').hidden=true;$('frameA').src=state.sequenceImages[i];
    $('frameA').alt=`SPHEREx archival observation ${i+1} of ${state.sequence.length}, ${fmtDate(ob.date_utc)}`;
    $('imageLegend').textContent='Common intensity stretch across all selected frames · NOT flux-calibrated comparison';
    $('viewModeText').textContent=`TIME SEQUENCE / ${i+1} OF ${state.sequenceImages.length}`;
    $('epochHud').textContent='UTC '+fmtDate(ob.date_utc);
    $('downloadPng').disabled=false;updateSequenceChips();return;
  }
  if(!state.images.a)return;
  const a=$('frameA'),b=$('frameB'),pane=$('imagePane');
  $('emptyStage').hidden=true;$('imageError').hidden=true;pane.hidden=false;
  pane.classList.toggle('split',state.mode==='split'&&!!state.b);
  b.hidden=!(state.mode==='split'&&state.b);
  $('imgBoxB').hidden=!(state.mode==='split'&&state.b);
  if(state.mode==='difference'){
    a.src=state.images.difference||state.images.a;a.alt='B minus A signed pixel residual visualization';
    $('imageLegend').textContent='AMBER: B brighter · CYAN: A brighter · exploratory residual';
    $('viewModeText').textContent='B − A / UNVERIFIED RESIDUAL';
  } else if(state.mode==='mean'){
    a.src=state.images.mean||state.images.a;a.alt='Mean of registered SPHEREx frames';
    $('imageLegend').textContent='Mean of two registered images · visual only';$('viewModeText').textContent='MEAN / TWO EXPOSURES';
  } else if(state.mode==='split'){
    a.src=state.images.a;b.src=state.images.b||state.images.a;a.alt='SPHEREx frame A';b.alt='SPHEREx frame B';
    $('imageLegend').textContent='LEFT: A · RIGHT: B · same stretch';$('viewModeText').textContent='SPLIT / A AND B';
  } else {
    a.src=state.images[state.current]||state.images.a;
    $('imageLegend').textContent='Shared intensity scale across both frames · asinh display stretch';
    $('viewModeText').textContent=`BLINK / FRAME ${state.current.toUpperCase()}`;
  }
  const current=state.current==='b'&&state.b?state.b:state.a;
  $('epochHud').textContent='UTC  '+fmtDate(state.mode==='difference'||state.mode==='mean'?state.b?.date_utc:current?.date_utc);
  $('downloadPng').disabled=!a.src;
  $('gaiaToggle').disabled=!(a.src&&state.mode!=='difference');
  if(state.catalogVisible&&state.mode!=='difference')drawCatalogOverlay();else clearCatalogOverlay();
}
function selectMode(mode){
  if(mode==='sequence' && state.sequence.length<2){
    setQueryStatus('Add two or more exposures using the + controls, then select Sequence.',true);
    return;
  }
  if(mode==='difference' && state.a && state.b && state.a.band!==state.b.band){
    $('imageError').textContent='Difference preview requires matching detector ranges. Select another Frame B. Even matching ranges do not guarantee identical per-pixel wavelengths.';
    $('imageError').hidden=false;return;
  }
  stop();state.mode=mode;state.current='a';document.querySelectorAll('.mode-button').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));
  updateInspector();updateTransport();
  if(!state.a && mode!=='sequence')return;
  renderImages();
}
function togglePlay(){
  if(state.playing){stop();return;}
  if(state.mode==='sequence'){
    if(state.sequenceImages.length<2)return;
    state.playing=true;$('playSymbol').textContent='Ⅱ';
    const tick=()=>{state.sequenceIndex=(state.sequenceIndex+1)%state.sequenceImages.length;showRendered();};
    tick();state.clock=setInterval(tick,Number($('speedSelect').value));return;
  }
  if(!state.a||!state.b)return;
  if(state.mode!=='blink')selectMode('blink');
  if(!state.images.a||!state.images.b)return;
  state.playing=true;$('playSymbol').textContent='Ⅱ';
  const tick=()=>{state.current=state.current==='a'?'b':'a';showRendered();};
  tick();state.clock=setInterval(tick,Number($('speedSelect').value));
}
const ATLAS_SURVEY_STATE={failed:new Set()};
function currentAtlasSource(){
  const sel=$('atlasSource');return sel?sel.value:'irsawise';
}
function setAtlasStatus(kind, message){
  const el=$('atlasStatus');if(!el)return;
  el.textContent=message;
  el.className='atlas-status '+kind;
}
function loadIrsaReferenceImage(){
  // IRSA-backed reference FITS: served by our own backend, so it works on any
  // network that can reach this app (no CDS dependency).  Two layers: a wide
  // ~1.25-deg context image underneath and the sharp field cutout on top.
  const fallback=$('atlasFallback'), text=$('atlasFallbackText'), retry=$('atlasRetry');
  const {ra,dec,fov}=coord();
  if(fallback){fallback.hidden=true;}
  const a=state.atlas;
  if(!a){return;}
  a.removeLayers();
  setAtlasStatus('loading','Loading AllWISE W1 (3.4 µm) from IRSA…');
  const base=`/api/atlas_image?ra=${ra}&dec=${dec}&ref=wise`;
  const detailFov=Math.min(fov,60);
  // Aladin Lite v3: displayFITS(url, layerName, successCallback, errorCallback)
  let pending=2;
  const done=()=>{
    pending-=1;
    if(pending===0){
      a.gotoRaDec(ra,dec);
      a.setFov(detailFov/60);
      setAtlasStatus('ok','✓ AllWISE W1 · 3.4 µm · mid-infrared · IRSA — detail on top, ~1.25° context beneath (zoom out to see it)');
    }
  };
  a.displayFITS(`${base}&fov=${detailFov}&tier=detail`, 'irsa-detail', done, ()=>{
    if(fallback){fallback.hidden=false;}
    if(text)text.textContent='Reference imagery is temporarily unavailable from IRSA (the archive did not respond). Press Load to retry — the SPHEREx data tools are unaffected.';
    if(retry)retry.hidden=false;
    setAtlasStatus('error','✗ IRSA did not respond — press Load to retry');
  });
  a.displayFITS(`${base}&tier=context`, 'irsa-context', done, ()=>{
    pending-=1; // context is optional: detail alone still works
  });
  a.gotoRaDec(ra,dec);a.setFov(detailFov/60);
}
function switchAtlasSource(){
  const src=currentAtlasSource();
  if(!state.atlas){state.atlas=null;updateAtlas();return;}
  if(src==='irsawise'){loadIrsaReferenceImage();return;}
  // CDS HiPS source: probe reachability first (the backend shares the same
  // network egress as this browser). Blocked networks fall back to IRSA
  // instead of silently keeping the previous image.
  setAtlasStatus('loading','Checking CDS reachability…');
  const host=src.startsWith('http')?'alasky.cds.unistra.fr':'alasky.cds.unistra.fr';
  fetch(`/api/net_check?host=${host}`,{headers:{Accept:'application/json'}})
    .then(r=>r.json())
    .then(({reachable})=>{
      if(!reachable){
        setAtlasStatus('error','✗ CDS tile servers are unreachable on this network — loaded AllWISE W1 · IRSA instead');
        loadIrsaReferenceImage();
        return;
      }
      setAtlasStatus('loading','CDS reachable — loading HiPS survey…');
      try{state.atlas.removeLayers();}catch{}
      try{
        state.atlas.setBaseImageLayer(src);
        const {ra,dec,fov}=coord();state.atlas.gotoRaDec(ra,dec);state.atlas.setFov(fov/60);
        $('atlasFallback').hidden=true;
        setAtlasStatus('loading','HiPS loading from CDS — tiles stream in gradually');
      }catch(e){setAtlasStatus('error','✗ Could not start the CDS survey');}
    })
    .catch(()=>{setAtlasStatus('error','✗ Reachability check failed — loaded AllWISE W1 · IRSA instead');loadIrsaReferenceImage();});
}
function updateAtlas(){
  const {ra,dec,fov}=coord();
  if(state.atlas){try{state.atlas.gotoRaDec(ra,dec);state.atlas.setFov(fov/60);}catch{}return;}
  if(state.atlasInitializing)return;
  const fallback=$('atlasFallback'), text=$('atlasFallbackText'), retry=$('atlasRetry');
  const showFallback=(message,offerRetry)=>{if(fallback){fallback.hidden=false;if(text)text.textContent=message;if(retry)retry.hidden=!offerRetry;}};
  const startInit=()=>{
    if(!window.A||!window.A.init){showFallback('Atlas engine could not be loaded.',true);return;}
    state.atlasInitializing=true;
    window.A.init.then(()=>{
      if(state.atlas)return;
      const a=window.A.aladin('#aladin-lite-div',{
        target:`${ra} ${dec}`,fov:fov/60,
        showReticle:true,reticleColor:'#d7c39c',showFullscreenControl:true,
        showLayersControl:false,showZoomControl:true,showGotoControl:false
      });
      state.atlas=a;if(fallback)fallback.hidden=true;
      // Default to the IRSA-backed reference image: no third-party tile server needed.
      loadIrsaReferenceImage();
    }).catch(()=>showFallback('The atlas engine could not initialise in this browser.',true))
      .finally(()=>{state.atlasInitializing=false;});
  };
  if(window.A&&window.A.init){if(retry)retry.hidden=true;startInit();return;}
  // The engine is served locally with the app; wait briefly for the module script.
  showFallback('Loading the atlas engine…',false);
  if(state.atlasWaiter)clearInterval(state.atlasWaiter);
  let waited=0;
  state.atlasWaiter=setInterval(()=>{
    waited+=250;
    if(window.A&&window.A.init){clearInterval(state.atlasWaiter);state.atlasWaiter=null;startInit();}
    else if(waited>10000){clearInterval(state.atlasWaiter);state.atlasWaiter=null;
      showFallback('Atlas engine did not start. Check that /vendor/aladin.js is served, then retry.',true);}
  },250);
}
function switchTab(tab){
  state.tab=tab;const atlas=tab==='atlas';
  $('frameStage').hidden=atlas;$('atlasStage').hidden=!atlas;
  // hidden on the science stage is HTML presentational here; flex CSS requires explicit override.
  $('frameStage').style.display=atlas?'none':'flex';
  document.querySelectorAll('.viewer-tab').forEach(b=>{const active=b.dataset.tab===tab;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));});
  if(atlas)updateAtlas();
}
function exportPng(){
  if(state.mode==='sequence'){
    const url=state.sequenceImages[state.sequenceIndex];if(!url)return;
    const link=el('a');link.href=url;link.download=`spherex_${state.release}_sequence_${state.sequenceIndex+1}_${fmtDate(state.sequence[state.sequenceIndex].date_utc)}_preview.png`;
    document.body.append(link);link.click();link.remove();return;
  }
  const mode=state.mode==='difference'?'difference':state.mode==='mean'?'mean':state.current==='b'?'b':'a';
  const url=state.images[mode]||state.images.a;if(!url)return;
  const link=el('a');link.href=url;link.download=`spherex_${state.release}_${mode}_${fmtDate(state.a?.date_utc)}_visual_preview.png`;document.body.append(link);link.click();link.remove();
}
function viewParams(){
  const {ra,dec,fov}=coord();
  const params=new URLSearchParams({ra:String(ra),dec:String(dec),fov:String(fov),release:state.release,survey:$('surveySelect').value,band:$('bandSelect').value,
    mode:state.mode,view:'1'});
  if($('startDate').value)params.set('start_date',$('startDate').value);
  if($('endDate').value)params.set('end_date',$('endDate').value);
  if(state.a)params.set('a_id',state.a.id);
  if(state.b)params.set('b_id',state.b.id);
  if(state.sequence.length)params.set('sequence',state.sequence.map(ob=>ob.id).join(','));
  return params;
}
async function copyView(){
  const uri=new URL(location.href);uri.search=viewParams().toString();
  try{await navigator.clipboard.writeText(uri.toString());$('shareBtn').textContent='Link copied';}
  catch{$('shareBtn').textContent='Copy unavailable';}
  setTimeout(()=>$('shareBtn').textContent='Copy view link',1600);
}
function reproducibleViewUrl(){
  try{return new URL('?'+viewParams().toString(),location.href).href;}
  catch{return null;} // Embedded screenshot previews have no navigable web origin.
}
function exportEvidence(){
  const {ra,dec,fov}=coord();
  const manifest={
    schema:'spherex-motion-explorer.evidence.v1',created_utc:new Date().toISOString(),
    instrument:'SPHEREx',independent_tool_version:'0.5.0',archive:'NASA/IPAC IRSA',
    dataset_release:state.release.toUpperCase(), survey_programme:$('surveySelect').value,
    dataset_doi:state.release==='qr3'?'10.26131/IRSA662':'10.26131/IRSA652',
    centre_icrs_deg:{ra,dec},fov_arcmin:fov,
    utc_filter:{start:$('startDate').value||null,end:$('endDate').value||null},
    observation_A:state.a||null,observation_B:state.b||null,
    chronological_sequence:state.sequence.map(({token,...ob})=>ob),
    exploratory_spectrum:state.spectrum?{ra:state.spectrum.ra,dec:state.spectrum.dec,
      points:state.spectrum.points,method:state.spectrum.method,caveat:state.spectrum.caveat}:null,
    // Tokens are links to public IRSA files; exclude from exported manifest.
    science_processing:state.mode==='sequence'?(state.sequenceMetadata||null):(state.imageMetadata||null),
    view_mode:state.mode,
    reproducible_view_url:reproducibleViewUrl(),
    input_fits_sha256:'not_computed_by_preview',
    limitations:['Not a discovery confirmation','Local wavelengths may differ between exposures',
      'PSF not matched; no calibrated difference noise','No significant-motion or parallax fit'],
    citation:'NASA/IPAC IRSA SPHEREx archive; follow the official data-release acknowledgement requirements.'
  };
  if(manifest.observation_A)delete manifest.observation_A.token;
  if(manifest.observation_B)delete manifest.observation_B.token;
  if(manifest.science_processing){
    // IRSA source URLs are included for auditability; all URLs point to the official archive.
  }
  const blob=new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'});
  const link=el('a');const url=URL.createObjectURL(blob);
  link.href=url;link.download=`spherex_evidence_${new Date().toISOString().slice(0,10)}.json`;
  document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
async function fetchSpectrum(){
  if(state.spectrumBusy)return;
  try{validate();}catch(error){setQueryStatus(error.message,true);return;}
  const queryId=++state.spectrumCounter;
  state.spectrumBusy=true;$('spectrumButton').disabled=true;
  const plot=$('spectrumPlot');plot.replaceChildren();
  const busy=el('div','spectrum-busy');busy.append(Object.assign(el('span','spinner')));
  busy.append(el('span','','Downloading many archive exposures and extracting aperture photometry… this can take one to three minutes.'));
  plot.append(busy);
  const {ra,dec,fov}=coord();
  const params=new URLSearchParams({ra:String(ra),dec:String(dec),fov:String(Math.min(fov,8)),release:state.release,survey:$('surveySelect').value,max_files:'40'});
  if($('startDate').value)params.set('start_date',$('startDate').value);
  if($('endDate').value)params.set('end_date',$('endDate').value);
  try{
    const response=await fetch('/api/spectrum?'+params,{headers:{Accept:'application/json'}});
    const payload=await response.json();
    if(queryId!==state.spectrumCounter)return;
    if(!response.ok)throw Error(payload.detail||`Spectrum extraction failed (${response.status})`);
    state.spectrum=payload;drawSpectrumPlot();
    setQueryStatus(`Spectrum: ${payload.points.length} wavelength points from ${payload.files_requested} exposures (${payload.files_failed_count} unusable).`);
  }catch(error){if(queryId===state.spectrumCounter){state.spectrum=null;plot.replaceChildren(el('div','wavelength-empty',error.message));}}
  finally{if(queryId===state.spectrumCounter){state.spectrumBusy=false;$('spectrumButton').disabled=false;}}
}
function drawSpectrumPlot(){
  const plot=$('spectrumPlot'),legend=$('spectrumLegend');
  legend.hidden=true;legend.replaceChildren();plot.replaceChildren();
  const points=(state.spectrum?.points||[]).filter(p=>Number.isFinite(p.lambda_um)&&Number.isFinite(p.flux_MJy_sr));
  $('spectrumCsv').disabled=!points.length;
  if(!points.length){plot.append(el('div','wavelength-empty',state.spectrum?'No valid spectrum points in these exposures. Adjust dates or try the other release.':'No spectrum extracted yet. Points are never simulated.'));return;}
  const W=760,H=270,L=58,R=14,T=14,B=40;
  const lamMin=0.7,lamMax=5.05;
  const fluxes=points.map(p=>p.flux_MJy_sr);
  fluxes.sort((a,b)=>a-b);
  const fLo=Math.max(0,fluxes[Math.floor(fluxes.length*0.02)]*0.9);
  const fHi=fluxes[Math.floor(fluxes.length*0.98)]*1.1||fluxes.at(-1);
  const X=l=>L+(l-lamMin)/(lamMax-lamMin)*(W-L-R);
  const Y=f=>T+(1-(f-fLo)/Math.max(1e-9,fHi-fLo))*(H-T-B);
  const svgNS='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(svgNS,'svg');
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.setAttribute('class','spectrum-svg');
  const mk=(tag,attrs)=>{const n=document.createElementNS(svgNS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);return n;};
  svg.append(mk('line',{x1:L,y1:H-B,x2:W-R,y2:H-B,stroke:'#3a4657'}));
  svg.append(mk('line',{x1:L,y1:T,x2:L,y2:H-B,stroke:'#3a4657'}));
  for(let l=1;l<=5;l++){svg.append(mk('line',{x1:X(l),y1:T,x2:X(l),y2:H-B,stroke:'#26303f','stroke-dasharray':'3 5'}));
    const t=mk('text',{x:X(l),y:H-B+18,'text-anchor':'middle',fill:'#8fa0b5','font-size':'11'});t.textContent=l+' µm';svg.append(t);}
  for(let k=0;k<=4;k++){const f=fLo+(fHi-fLo)*k/4,y=Y(fLo+(fHi-fLo)*k/4);
    svg.append(mk('line',{x1:L,y1:y,x2:W-R,y2:y,stroke:'#26303f','stroke-dasharray':'3 5'}));
    const t=mk('text',{x:L-6,y:y+4,'text-anchor':'end',fill:'#8fa0b5','font-size':'10'});
    t.textContent=f>=1000?(f/1000).toFixed(1)+'k':f.toFixed(f<10?1:0);svg.append(t);}
  const yl=mk('text',{x:14,y:H/2,fill:'#8fa0b5','font-size':'11',transform:`rotate(-90 14 ${H/2})`,'text-anchor':'middle'});yl.textContent='Aperture flux · MJy/sr';svg.append(yl);
  const usedDetectors=new Set();
  for(const p of points){
    const c=DETECTOR_COLORS[p.band]||DETECTOR_COLORS.Unknown;usedDetectors.add(p.band);
    const x=X(p.lambda_um),y=Y(p.flux_MJy_sr);
    if(p.err_stat_MJy_sr){const e=Y(p.flux_MJy_sr-p.err_stat_MJy_sr),e2=Y(Math.min(fHi,p.flux_MJy_sr+p.err_stat_MJy_sr));
      svg.append(mk('line',{x1:x,y1:e,x2:x,y2:e2,stroke:c,'stroke-width':1,opacity:.75}));
      svg.append(mk('line',{x1:x-3,y1:e,x2:x+3,y2:e,stroke:c,'stroke-width':1,opacity:.75}));
      svg.append(mk('line',{x1:x-3,y1:e2,x2:x+3,y2:e2,stroke:c,'stroke-width':1,opacity:.75}));}
    const dot=mk('circle',{cx:x,cy:Math.max(T,Math.min(H-B,y)),r:3.4,fill:c,opacity:.92});
    const tip=document.createElementNS(svgNS,'title');
    tip.textContent=`${p.lambda_um.toFixed(3)} µm · ${p.flux_MJy_sr.toFixed(2)} MJy/sr · SNR ${p.snr??'?'}\n${p.band} · ${p.obs_id||''}\n${p.date_utc?p.date_utc.slice(0,10):''}`;
    dot.append(tip);svg.append(dot);
  }
  plot.append(svg);
  legend.hidden=false;
  for(const band of ['D1','D2','D3','D4','D5','D6'])if(usedDetectors.has(band)){
    const chip=el('span','spectrum-det-chip');chip.append(Object.assign(el('i'),{style:`background:${DETECTOR_COLORS[band]}`}),el('span','',band));legend.append(chip);}
  const note=el('span','spectrum-det-note',`${points.length} points · hover for observation details`);legend.append(note);
}
function exportSpectrumCsv(){
  const points=state.spectrum?.points||[];if(!points.length)return;
  const head='lambda_um,bandwidth_um,flux_MJy_sr,err_stat_MJy_sr,snr,detector,obs_id,date_utc\n';
  const rows=points.map(p=>[p.lambda_um,p.bandwidth_um,p.flux_MJy_sr,p.err_stat_MJy_sr??'',p.snr??'',p.band,p.obs_id||'',p.date_utc||''].join(',')).join('\n');
  const blob=new Blob([head+rows+'\n'],{type:'text/csv'});
  const link=el('a');const url=URL.createObjectURL(blob);
  link.href=url;link.download=`spherex_spectrum_${state.spectrum.ra.toFixed(4)}_${state.spectrum.dec.toFixed(4)}.csv`;
  document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
async function toggleCatalogOverlay(){
  if(state.catalogVisible){state.catalogVisible=false;drawCatalogOverlay();return;}
  if(state.catalogBusy)return;
  state.catalogBusy=true;$('gaiaToggle').disabled=true;$('gaiaToggle').textContent='✦ Loading Gaia…';
  const {ra,dec,fov}=coord();
  try{
    const response=await fetch(`/api/catalog?ra=${ra}&dec=${dec}&fov=${fov}`,{headers:{Accept:'application/json'}});
    const payload=await response.json();
    if(!response.ok)throw Error(payload.detail||`Catalogue query failed (${response.status})`);
    state.catalog=payload;state.catalogVisible=true;drawCatalogOverlay();
    const highPm=payload.sources.filter(s=>(s.motion_arcsec_yr||0)>1).length;
    setQueryStatus(`Gaia overlay: ${payload.count} reference stars at epoch ${payload.epoch_year}${highPm?` · ${highPm} with motion >1″/yr`:''}.`);
  }catch(error){setQueryStatus(error.message,true);state.catalogVisible=false;}
  finally{state.catalogBusy=false;$('gaiaToggle').disabled=!state.images.a;$('gaiaToggle').textContent='✦ Gaia overlay';}
}
function skyFraction(ra,dec){
  const grid=state.imageMetadata?.display_grid||state.sequenceMetadata?.display_grid;if(!grid)return null;
  const ra0=Array.isArray(grid.crval)?grid.crval[0]:grid.ra;
  const dec0=Array.isArray(grid.crval)?grid.crval[1]:grid.dec;
  if(!Number.isFinite(ra0)||!Number.isFinite(dec0))return null;
  const dRa=(ra-ra0)*Math.cos(dec0*Math.PI/180),dDec=dec-dec0;
  const sx=dRa*3600/grid.pixel_scale_arcsec,sy=dDec*3600/grid.pixel_scale_arcsec;
  const cx=(grid.width+1)/2,cy=(grid.height+1)/2;
  // CDELT1 negative: RA increases leftward; PNG flipped vertically: north is up.
  const fx=(cx-1-sx)/grid.width, fy=1-(cy-1+sy)/grid.height;
  if(!Number.isFinite(fx)||!Number.isFinite(fy))return null;
  return {fx,fy};
}
function visibleOverlayTargets(){
  const imgs=[],pane=$('imagePane');
  const a=$('frameA'),b=$('frameB');
  if(a&&a.src&&!pane.hidden)imgs.push(a);
  if(b&&b.src&&!b.hidden&&pane.classList.contains('split'))imgs.push(b);
  return imgs;
}
function syncOverlayCanvas(img){
  // The canvas lives inside the frame's .img-box wrapper, so zoom/pan transforms
  // applied to the wrapper scale image and overlay together.
  const box=img.parentElement;
  let canvas=box.querySelector(`canvas[data-for="${img.id}"]`);
  if(!canvas){canvas=document.createElement('canvas');canvas.className='overlay-canvas';canvas.dataset.for=img.id;box.append(canvas);}
  const w=img.clientWidth,h=img.clientHeight;
  if(!w||!h||!img.naturalWidth){canvas.hidden=true;return null;}
  canvas.style.position='absolute';canvas.style.left='0';canvas.style.top='0';
  canvas.style.width=w+'px';canvas.style.height=h+'px';
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  canvas.hidden=false;
  // The science image uses object-fit:contain; map into the letterboxed rect.
  const scale=Math.min(w/img.naturalWidth,h/img.naturalHeight);
  const dw=img.naturalWidth*scale,dh=img.naturalHeight*scale;
  return {canvas,w,h,ox:(w-dw)/2,oy:(h-dh)/2,dw,dh};
}
function paintCatalog(ctx,pair){
  const {w,h,ox,oy,dw,dh}=pair;
  ctx.clearRect(0,0,w,h);
  const magRange=[17.5,8];
  const grid=state.imageMetadata?.display_grid||state.sequenceMetadata?.display_grid;
  for(const s of state.catalog.sources){
    const frac=skyFraction(s.ra_propagated,s.dec_propagated);if(!frac)continue;
    const px=ox+frac.fx*dw,py=oy+frac.fy*dh;
    if(px<ox-10||py<oy-10||px>ox+dw+10||py>oy+dh+10)continue;
    const gm=s.g_mag??16;
    const r=Math.max(3,Math.min(11,4.5+(magRange[0]-gm)*0.62));
    const hot=(s.motion_arcsec_yr||0)>1;
    ctx.strokeStyle=hot?'#ffc46b':'#59d2ff';ctx.lineWidth=hot?2:1.2;
    ctx.beginPath();ctx.arc(px,py,r,0,Math.PI*2);ctx.stroke();
    if(hot&&s.pmra_mas_yr!=null){
      const EXAG=50; // annual-motion arrows exaggerated, stated in the caption
      const dGridX=-s.pmra_mas_yr/1000/grid.pixel_scale_arcsec;   // east is left
      const dGridY= s.pmdec_mas_yr/1000/grid.pixel_scale_arcsec;  // north is grid +y
      const dx=dGridX/grid.width*dw*EXAG;
      const dy=-dGridY/grid.height*dh*EXAG;                       // canvas y flips
      ctx.beginPath();ctx.moveTo(px,py);ctx.lineTo(px+dx,py+dy);ctx.stroke();
      ctx.font='10px monospace';
      const label=`${s.motion_arcsec_yr.toFixed(1)}″/yr`;
      const lw=ctx.measureText(label).width;
      ctx.fillStyle='rgba(6,14,22,0.72)';ctx.fillRect(px+r+2,py-16,lw+6,13);
      ctx.fillStyle='#ffc46b';ctx.fillText(label,px+r+5,py-5);
    }
  }
  ctx.font='10px monospace';
  const caption=`Gaia DR3 · epoch ${state.catalog.epoch_year} · circles = reference stars · amber = motion >1″/yr (arrow ×50)`;
  const tw=ctx.measureText(caption).width;
  const boxW=Math.min(tw+10,w-8);
  ctx.fillStyle='rgba(6,14,22,0.78)';ctx.fillRect(4,h-20,boxW,16);
  ctx.fillStyle='#7fd6ff';ctx.fillText(caption,9,h-8);
}
function drawCatalogOverlay(){
  const pane=$('imagePane');
  if(!state.catalogVisible||!state.catalog||pane.hidden){
    pane.querySelectorAll('canvas.overlay-canvas').forEach(c=>c.hidden=true);return;
  }
  const wanted=new Set();
  for(const img of visibleOverlayTargets()){
    const pair=syncOverlayCanvas(img);if(!pair)continue;
    wanted.add(pair.canvas);
    paintCatalog(pair.canvas.getContext('2d'),pair);
  }
  // Hide (not recreate) stale canvases: blink playback calls this every tick.
  pane.querySelectorAll('canvas.overlay-canvas').forEach(c=>{if(!wanted.has(c))c.hidden=true;});
}
function clearCatalogOverlay(){
  state.catalogVisible=false;
  const pane=$('imagePane');
  if(pane)pane.querySelectorAll('canvas.overlay-canvas').forEach(c=>c.remove());
}
/* ---- science-frame zoom & pan (image + Gaia overlay scale together) ---- */
function applyFrameTransform(){
  const t=`translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
  for(const id of ['imgBoxA','imgBoxB']){
    const box=$(id);if(!box)continue;
    box.style.transform=t;
  }
  $('viewportResolution')?.replaceChildren(`FOV ${coord().fov}′ × ${coord().fov}′${state.zoom>1?` · zoom ${state.zoom.toFixed(1)}×`:''}`);
}
function setFrameZoom(z, keepPan=true){
  const nz=Math.min(6, Math.max(1, z));
  if(!keepPan || nz===1){state.panX=0;state.panY=0;}
  state.zoom=nz;applyFrameTransform();
}
function initFrameZoom(){
  $('zoomIn').addEventListener('click',()=>setFrameZoom(state.zoom*1.4));
  $('zoomOut').addEventListener('click',()=>setFrameZoom(state.zoom/1.4));
  $('zoomReset').addEventListener('click',()=>setFrameZoom(1,false));
  const stage=$('frameStage');
  stage.addEventListener('wheel',event=>{
    if($('imagePane').hidden)return;
    event.preventDefault();
    setFrameZoom(state.zoom*(event.deltaY<0?1.15:1/1.15));
  },{passive:false});
  let dragging=null;
  stage.addEventListener('pointerdown',event=>{
    if($('imagePane').hidden||state.zoom<=1)return;
    dragging={x:event.clientX,y:event.clientY,px:state.panX,py:state.panY};
    stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove',event=>{
    if(!dragging)return;
    state.panX=dragging.px+(event.clientX-dragging.x);
    state.panY=dragging.py+(event.clientY-dragging.y);
    applyFrameTransform();
  });
  const end=()=>{dragging=null;};
  stage.addEventListener('pointerup',end);stage.addEventListener('pointercancel',end);
}
function init(){
  const qs=new URLSearchParams(location.search);
  if(qs.has('ra')&&qs.has('dec')){
    $('targetPreset').value='custom';$('raInput').value=qs.get('ra');$('decInput').value=qs.get('dec');
    $('fieldName').textContent='Custom sky field';$('epochNote').textContent='User supplied ICRS coordinates. Reference epoch, if relevant, must be supplied by the observer.';
    const fov=Number(qs.get('fov'));if(fov>=1&&fov<=18)$('fovInput').value=String(fov);
  }else{setTarget('barnard');}
  if(['qr3','qr2'].includes(qs.get('release')))$('releaseSelect').value=qs.get('release');
  if(['wide','deep'].includes(qs.get('survey')))$('surveySelect').value=qs.get('survey');
  if(['all','D1','D2','D3','D4','D5','D6','Unknown'].includes(qs.get('band')))$('bandSelect').value=qs.get('band');
  state.release=$('releaseSelect').value;
  if(/^\d{4}-\d{2}-\d{2}$/.test(qs.get('start_date')||''))$('startDate').value=qs.get('start_date');
  if(/^\d{4}-\d{2}-\d{2}$/.test(qs.get('end_date')||''))$('endDate').value=qs.get('end_date');
  if(qs.get('view')==='1')state.pendingView=Object.fromEntries(qs.entries());
  $('fovValue').textContent=$('fovInput').value+' arcmin';updateCoords();updateInspector();
  $('targetPreset').addEventListener('change',event=>{
    if(event.target.value==='custom'){$('fieldName').textContent='Custom sky field';$('epochNote').textContent='Coordinates entered manually; ensure the reference epoch is appropriate.';return;}
    setTarget(event.target.value);resetPair();
  });
  for(const field of ['raInput','decInput'])$(field).addEventListener('change',()=>{if($('targetPreset').value!=='custom'){$('targetPreset').value='custom';$('fieldName').textContent='Custom sky field';}$('epochNote').textContent='User-specified coordinates; no proper-motion propagation applied.';updateCoords();resetPair();});
  $('fovInput').addEventListener('input',()=>{$('fovValue').textContent=$('fovInput').value+' arcmin';updateCoords();});
  $('fovInput').addEventListener('change',resetPair);
  $('searchButton').addEventListener('click',search);
  $('baselineButton').addEventListener('click',chooseWidestBaseline);
  $('bandSelect').addEventListener('change',()=>{stop();resetPair();filterObservations();});
  $('clearSequence').addEventListener('click',clearSequenceSelection);
  $('exportEvidence').addEventListener('click',exportEvidence);
  for(const dateId of ['startDate','endDate'])$(dateId).addEventListener('change',()=>{
    resetPair();state.allResults=[];state.observations=[];drawObservations();
    setQueryStatus('UTC date filter changed; retrieve observations again.');
  });
  $('surveySelect').addEventListener('change',()=>{resetPair();state.allResults=[];state.observations=[];drawObservations();setQueryStatus('Survey programme changed. Retrieve observations again.');});
  $('releaseSelect').addEventListener('change',()=>{state.release=$('releaseSelect').value;resetPair();state.allResults=[];state.observations=[];drawObservations();setQueryStatus('Release changed. Retrieve observations to load matching archive data.');});
  $('playBtn').addEventListener('click',togglePlay);
  $('spectrumButton').addEventListener('click',fetchSpectrum);
  $('spectrumCsv').addEventListener('click',exportSpectrumCsv);
  $('gaiaToggle').addEventListener('click',toggleCatalogOverlay);
  window.addEventListener('resize',()=>{if(state.catalogVisible)drawCatalogOverlay();});
  $('speedSelect').addEventListener('change',()=>{if(state.playing){stop();togglePlay();}});
  document.querySelectorAll('.mode-button').forEach(b=>b.addEventListener('click',()=>selectMode(b.dataset.mode)));
  document.querySelectorAll('.viewer-tab').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));
  $('shareBtn').addEventListener('click',copyView);$('downloadPng').addEventListener('click',exportPng);
  $('atlasRetry').addEventListener('click',()=>{$('atlasFallback').hidden=true;loadIrsaReferenceImage();});
  $('atlasSource').addEventListener('change',switchAtlasSource);
  $('atlasReload').addEventListener('click',()=>switchAtlasSource());
  $('atlasMin').addEventListener('click',()=>{
    state.atlasMinimized=!state.atlasMinimized;
    $('atlasHeader').classList.toggle('min',state.atlasMinimized);
    $('atlasMin').textContent=state.atlasMinimized?'▸':'▾';
    $('atlasMin').setAttribute('aria-expanded',String(!state.atlasMinimized));
  });
  initFrameZoom();
  document.addEventListener('keydown',event=>{
    if(['INPUT','SELECT','TEXTAREA','BUTTON'].includes(document.activeElement?.tagName))return;
    if(event.code==='Space'&&state.a&&state.b){event.preventDefault();togglePlay();}
    if(event.key==='Escape')stop();
  });
  if(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches){$('speedSelect').value='1200';}
  // Navigation performs real focus/switch actions, not inert tab decoration.
  const railButtons=[...document.querySelectorAll('[data-nav]')];
  function activateNav(action){
    railButtons.forEach(btn=>{const active=btn.dataset.nav===action;btn.classList.toggle('active',active);
      if(active)btn.setAttribute('aria-current','page');else btn.removeAttribute('aria-current');});
    if(action==='explore'){$('queryPanel').scrollIntoView({block:'nearest'});$('targetPreset').focus();}
    else if(action==='observations'){$('observationsPanel').scrollIntoView({block:'nearest'});$('observationList').scrollIntoView({block:'nearest'});}
    else if(action==='compare'){$('skyPanel').scrollIntoView({block:'nearest'});document.querySelector('.mode-switch').scrollIntoView({block:'nearest'});}
    else if(action==='atlas'){switchTab('atlas');$('skyPanel').scrollIntoView({block:'nearest'});}
    else if(action==='inspector'){$('inspectorPanel').scrollIntoView({block:'nearest'});}
  }
  railButtons.forEach(b=>b.addEventListener('click',()=>activateNav(b.dataset.nav)));
  $('emptyAction').addEventListener('click',()=>activateNav('explore'));
  $('helpBtn').addEventListener('click',()=>$('helpDialog').showModal());
  $('closeHelp').addEventListener('click',()=>$('helpDialog').close());
  $('helpDialog').addEventListener('click',e=>{if(e.target===$('helpDialog'))$('helpDialog').close();});
  document.addEventListener('keydown',event=>{
    if(event.key==='?'&&!['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName)){
      event.preventDefault();if(!$('helpDialog').open)$('helpDialog').showModal();
    }
  });
  for(const id of ['raInput','decInput','startDate','endDate'])$(id).addEventListener('keydown',e=>{
    if(e.key==='Enter'){e.preventDefault();$('searchButton').click();}
  });
  updateSciencePanels();drawTimeline();updateSequenceChips();
  if(state.pendingView)search();
}
init();
