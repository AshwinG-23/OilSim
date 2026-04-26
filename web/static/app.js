'use strict';

// ── Palette ───────────────────────────────────────────────────────────────────
const SC = {          // strategy colors
  cost_focused: '#2563eb',
  diversified:  '#16a34a',
  resilient:    '#d97706',
  adaptive:     '#7c3aed',
};
const SL = {          // strategy labels
  cost_focused: 'Cost Focused',
  diversified:  'Diversified',
  resilient:    'Resilient',
  adaptive:     'Adaptive',
};
const SRC_C = {       // source colors
  Gulf:          '#2563eb',
  Russia:        '#7c3aed',
  Africa:        '#16a34a',
  Gulf_Pipeline: '#d97706',
};

Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size   = 11;
Chart.defaults.color       = '#99a0ae';

// ── State ─────────────────────────────────────────────────────────────────────
const S = {
  meta:          null,
  scenarios:     ['short_conflict'],   // array — supports multi-select
  strategies:    ['cost_focused', 'resilient'],
  days:          90,
  reps:          30,
  flags:         {},
  result:        null,
  srcStrategy:   null,
};

// ── Charts ────────────────────────────────────────────────────────────────────
const C = { shortage:null, cost:null, dfr:null, fleet:null, inventory:null, source:null };

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmt  = s => s.replace(/_/g,' ').replace(/\b\w/g, c=>c.toUpperCase());
const fmtS = s => SL[s] || fmt(s);
const rgba = (hex, a) => {
  const [r,g,b] = [hex.slice(1,3),hex.slice(3,5),hex.slice(5,7)].map(x=>parseInt(x,16));
  return `rgba(${r},${g},${b},${a})`;
};
const sc   = s => SC[s] || '#99a0ae';
const dfrC = v => v>=95?'#16a34a':v>=85?'#d97706':'#dc2626';
const fltC = v => v<70?'#16a34a':v<85?'#d97706':'#dc2626';

// Shared axis style
const ax = (title, cb) => ({
  grid:  { color:'#f0f1f3' },
  ticks: { color:'#99a0ae', font:{size:10.5}, ...(cb?{callback:cb}:{}) },
  title: title?{display:true,text:title,color:'#99a0ae',font:{size:10.5}}:{display:false},
});
const axNoGrid = () => ({ grid:{display:false}, ticks:{color:'#525866',font:{size:10.5}} });

// ── Init charts ───────────────────────────────────────────────────────────────
function initCharts() {
  C.shortage = new Chart($('chart-shortage'), {
    type:'bar',
    data:{ labels:[], datasets:[{ data:[], borderWidth:0, borderRadius:3 }] },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:ctx=>`${ctx.raw.toLocaleString()} h`}} },
      scales:{ x:{...ax('Shortage Hours'), beginAtZero:true}, y:axNoGrid() },
    },
  });

  C.cost = new Chart($('chart-cost'), {
    type:'bar',
    data:{ labels:[], datasets:[{ data:[], borderWidth:0, borderRadius:3 }] },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:ctx=>`$${ctx.raw.toFixed(2)}/bbl`}} },
      scales:{ y:{...ax('$/bbl'), beginAtZero:false}, x:axNoGrid() },
    },
  });

  C.dfr = new Chart($('chart-dfr'), {
    type:'bar',
    data:{ labels:[], datasets:[{ data:[], borderWidth:0, borderRadius:3 }] },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:ctx=>`${ctx.raw.toFixed(1)}%`}} },
      scales:{
        x:{ ...ax('Fulfillment %'), min:0, max:100, ticks:{callback:v=>v+'%',color:'#99a0ae',font:{size:10.5}} },
        y:axNoGrid(),
      },
    },
  });

  C.fleet = new Chart($('chart-fleet'), {
    type:'bar',
    data:{ labels:[], datasets:[{ data:[], borderWidth:0, borderRadius:3 }] },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false}, tooltip:{callbacks:{label:ctx=>`${ctx.raw.toFixed(1)}%`}} },
      scales:{
        y:{ ...ax('Utilization %'), min:0, max:100, ticks:{callback:v=>v+'%',color:'#99a0ae',font:{size:10.5}} },
        x:axNoGrid(),
      },
    },
  });

  // Inventory line + custom ref-line plugin
  const refLines = {
    id:'refLines',
    beforeDraw(ch) {
      const {ctx,chartArea:ca,scales:{y}} = ch;
      if (!ca||!y) return;
      ctx.save();
      [{val:30,color:'#d97706',lbl:'Reorder'},{val:10,color:'#dc2626',lbl:'Critical'}].forEach(({val,color,lbl})=>{
        const yp = y.getPixelForValue(val);
        if (yp<ca.top||yp>ca.bottom) return;
        ctx.strokeStyle=color; ctx.setLineDash([5,4]); ctx.lineWidth=1;
        ctx.beginPath(); ctx.moveTo(ca.left,yp); ctx.lineTo(ca.right,yp); ctx.stroke();
        ctx.setLineDash([]); ctx.fillStyle=color; ctx.font='10px Inter,system-ui';
        ctx.textAlign='right'; ctx.fillText(lbl,ca.right-4,yp-3);
      });
      ctx.restore();
    },
  };

  C.inventory = new Chart($('chart-inventory'), {
    type:'line',
    data:{ labels:[], datasets:[] },
    options:{
      responsive:true, maintainAspectRatio:false,
      interaction:{ mode:'index', intersect:false },
      plugins:{
        legend:{
          display:true,
          labels:{
            filter: item=>!item.text.includes('__b'),
            color:'#525866', font:{size:11}, boxWidth:18, padding:14,
          },
        },
        tooltip:{
          filter: item=>!item.dataset.label.includes('__b'),
          callbacks:{
            label: ctx=> ctx.dataset.type==='scatter'
              ? `⚡ Disruption`
              : `${fmtS(ctx.dataset.label)}: ${ctx.raw.toFixed(2)}M bbl`,
          },
        },
      },
      scales:{
        x:{ ...ax('Day'), ticks:{maxTicksLimit:14,color:'#99a0ae',font:{size:10.5}} },
        y:{ ...ax('Inventory (M bbl)'), min:0 },
      },
    },
    plugins:[refLines],
  });

  C.source = new Chart($('chart-source'), {
    type:'doughnut',
    data:{ labels:[], datasets:[{ data:[], backgroundColor:[], borderWidth:2, borderColor:'#fff', hoverOffset:6 }] },
    options:{
      responsive:true, maintainAspectRatio:false, cutout:'66%',
      plugins:{
        legend:{ position:'right', labels:{color:'#525866',padding:10,font:{size:11},boxWidth:12} },
        tooltip:{
          callbacks:{
            label: ctx=>{
              const tot=ctx.dataset.data.reduce((a,b)=>a+b,0);
              const pct=tot>0?((ctx.raw/tot)*100).toFixed(1):'0.0';
              return `${ctx.label}: ${(ctx.raw/1e6).toFixed(1)}M bbl (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function renderSidebar() {
  const {meta} = S;

  // Scenarios — checkboxes (multi-select)
  const sl = $('scenario-list');
  const updateScCount = () => {
    const el = $('sc-count');
    if (el) el.textContent = S.scenarios.length > 1 ? `(${S.scenarios.length} combined)` : '';
  };
  meta.scenarios.forEach(name => {
    const lbl = document.createElement('label');
    lbl.className='opt';
    lbl.innerHTML=`<input type="checkbox" value="${name}" ${S.scenarios.includes(name)?'checked':''}><span>${fmt(name)}</span>`;
    lbl.querySelector('input').addEventListener('change', e => {
      if (e.target.checked) { if (!S.scenarios.includes(name)) S.scenarios.push(name); }
      else S.scenarios = S.scenarios.filter(s => s !== name);
      updateScCount();
    });
    sl.appendChild(lbl);
  });
  updateScCount();

  // Strategies
  const stl = $('strategy-list');
  meta.strategies.forEach(st => {
    const lbl = document.createElement('label');
    lbl.className='opt';
    lbl.innerHTML=`
      <input type="checkbox" value="${st}" ${S.strategies.includes(st)?'checked':''}>
      <span class="opt-dot" style="background:${sc(st)}"></span>
      <span>${fmtS(st)}</span>`;
    lbl.querySelector('input').addEventListener('change',e=>{
      if (e.target.checked) S.strategies.push(st);
      else S.strategies=S.strategies.filter(s=>s!==st);
    });
    stl.appendChild(lbl);
  });

  // Flags
  renderFlags();
}

function renderFlags() {
  const body = $('flags-body');
  body.innerHTML='';
  S.meta.feature_flags.forEach(flag=>{
    S.flags[flag.key]=false;
    flag.params.forEach(p=>{ S.flags[p.key]=p.default; });

    const div=document.createElement('div');
    div.className='flag-item';
    div.innerHTML=`
      <div class="flag-header">
        <span>${flag.label}</span>
        <label class="toggle">
          <input type="checkbox" data-key="${flag.key}">
          <span class="track"></span>
        </label>
      </div>
      ${flag.params.length?`<div class="flag-params" data-params="${flag.key}">
        ${flag.params.map(p=>`<div class="param-row"><span>${p.label}</span>
          <input type="number" data-p="${p.key}" value="${p.default}" min="1"></div>`).join('')}
      </div>`:''}`;

    const cb=div.querySelector(`input[data-key="${flag.key}"]`);
    const pm=div.querySelector(`[data-params="${flag.key}"]`);
    cb.addEventListener('change',()=>{
      S.flags[flag.key]=cb.checked;
      if (pm) pm.classList.toggle('show',cb.checked);
    });
    flag.params.forEach(p=>{
      const inp=div.querySelector(`input[data-p="${p.key}"]`);
      if (inp) inp.addEventListener('input',()=>{ S.flags[p.key]=parseFloat(inp.value)||p.default; });
    });
    body.appendChild(div);
  });
}

// ── Listeners ─────────────────────────────────────────────────────────────────
function attachListeners() {
  $('run-btn').addEventListener('click', run);

  const ds=$('dur-slider');
  ds.addEventListener('input',()=>{ S.days=+ds.value; $('dur-lbl').textContent=`${S.days} days`; });

  const rs=$('rep-slider');
  rs.addEventListener('input',()=>{ S.reps=+rs.value; $('rep-lbl').textContent=S.reps; });

  $('flags-btn').addEventListener('click',()=>{
    const b=$('flags-body'), ch=$('chevron');
    b.classList.toggle('open');
    ch.classList.toggle('open');
  });

  $('src-sel').addEventListener('change',e=>{
    S.srcStrategy=e.target.value;
    if (S.result) updateSrc(S.result,e.target.value);
  });
}

// ── Run ───────────────────────────────────────────────────────────────────────
async function run() {
  if (!S.scenarios.length) return setStatus('Select at least one scenario.','err');
  if (!S.strategies.length) return setStatus('Select at least one strategy.','err');

  setLoading(true);
  try {
    const r=await fetch('/api/run',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        scenarios:[...S.scenarios], strategies:[...S.strategies],
        duration_days:S.days, replications:S.reps,
        feature_flags:{...S.flags},
      }),
    });
    const d=await r.json();
    if (!r.ok) throw new Error(d.error||`HTTP ${r.status}`);
    S.result=d;
    S.srcStrategy=S.strategies[0];
    render(d);
    setStatus('');
  } catch(e) {
    setStatus(e.message,'err');
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  const btn=$('run-btn');
  btn.disabled=on;
  btn.textContent=on?'Running…':'Run Simulation';
  document.querySelectorAll('.kpi-val').forEach(el=>el.classList.toggle('skel',on));
  if (!on) document.querySelectorAll('.kpi-val').forEach(el=>el.classList.remove('skel'));
}
function setStatus(msg,cls='') {
  const el=$('run-status');
  el.textContent=msg;
  el.className=cls;
}

// ── Render ────────────────────────────────────────────────────────────────────
function render(d) {
  const strats=Object.keys(d.strategies);
  const kArr=strats.map(s=>d.strategies[s].kpis);

  // Title
  const scLabel = (d.scenarios||[d.scenario]).map(fmt).join(' + ');
  $('page-title').textContent=`${scLabel} — ${strats.map(fmtS).join(' · ')}`;
  $('run-meta').textContent=`${d.duration_days} days · ${d.replications} rep${d.replications!==1?'s':''}`;

  // KPIs
  const bShort=Math.min(...kArr.map(k=>k.mean_shortage_hours));
  const bDFR  =Math.max(...kArr.map(k=>k.mean_fulfillment_rate));
  const bCost =Math.min(...kArr.map(k=>k.mean_avg_cost_per_bbl));
  const avgFlt=kArr.reduce((s,k)=>s+k.mean_fleet_utilization,0)/kArr.length;
  const bTot  =Math.min(...kArr.map(k=>k.mean_total_cost));
  const fsArr =kArr.map(k=>k.first_shortage_hour).filter(Boolean);
  const bFirst=fsArr.length?Math.min(...fsArr):null;

  setKPI('kpi-shortage', bShort.toLocaleString(), 'hours',
    bShort<500?'good':bShort<2000?'warn':'bad');
  setKPI('kpi-dfr', `${(bDFR*100).toFixed(1)}%`, 'demand met',
    bDFR>=.95?'good':bDFR>=.85?'warn':'bad');
  setKPI('kpi-cost',  `$${bCost.toFixed(2)}`, '$/bbl transport', null);
  setKPI('kpi-fleet', `${(avgFlt*100).toFixed(1)}%`, 'avg utilization',
    avgFlt<.70?'good':avgFlt<.85?'warn':'bad');
  setKPI('kpi-totalcost', `$${(bTot/1e9).toFixed(2)}B`, 'total spend', null);
  setKPI('kpi-first',
    bFirst?`Day ${Math.floor(bFirst/24)}`:'None',
    bFirst?'first shortage event':'no shortages recorded',
    bFirst?'warn':'good');

  // Charts
  updateBars(d,strats);
  updateInv(d,strats);
  updateSrc(d,S.srcStrategy||strats[0]);

  // Source selector
  const sel=$('src-sel');
  sel.innerHTML=strats.map(s=>`<option value="${s}">${fmtS(s)}</option>`).join('');
  sel.value=S.srcStrategy||strats[0];
  sel.classList.toggle('hidden',strats.length<=1);

  // Table
  renderTable(d,strats);
}

function setKPI(id,val,sub,state) {
  const card=$(id);
  if (!card) return;
  card.querySelector('.kpi-val').textContent=val;
  card.querySelector('.kpi-sub').textContent=sub;
  card.className='kpi'+(state?` ${state}`:'');
}

// ── Bar charts ────────────────────────────────────────────────────────────────
function updateBars(d,strats) {
  const labels=strats.map(fmtS);
  const kArr=strats.map(s=>d.strategies[s].kpis);
  const colors=strats.map(sc);

  upd(C.shortage, labels, kArr.map(k=>Math.round(k.mean_shortage_hours)), colors);
  upd(C.cost,     labels, kArr.map(k=>+k.mean_avg_cost_per_bbl.toFixed(2)), colors);

  const dfr=kArr.map(k=>+(k.mean_fulfillment_rate*100).toFixed(2));
  upd(C.dfr, labels, dfr, dfr.map(dfrC));

  const flt=kArr.map(k=>+(k.mean_fleet_utilization*100).toFixed(1));
  upd(C.fleet, labels, flt, flt.map(fltC));
}
function upd(chart,labels,data,bg) {
  chart.data.labels=labels;
  chart.data.datasets[0].data=data;
  chart.data.datasets[0].backgroundColor=bg;
  chart.update();
}

// ── Inventory chart ───────────────────────────────────────────────────────────
function updateInv(d,strats) {
  const ds=[];
  const ts0=d.strategies[strats[0]].inventory_timeseries;

  strats.forEach(st=>{
    const ts=d.strategies[st].inventory_timeseries;
    const col=sc(st);
    ds.push({ label:`${st}__bu`, data:ts.upper, borderColor:'transparent',
      backgroundColor:rgba(col,.1), fill:'+1', tension:.35, pointRadius:0, borderWidth:0 });
    ds.push({ label:st, data:ts.mean, borderColor:col, backgroundColor:'transparent',
      fill:false, tension:.35, pointRadius:0, borderWidth:2 });
    ds.push({ label:`${st}__bl`, data:ts.lower, borderColor:'transparent',
      backgroundColor:rgba(col,.1), fill:false, tension:.35, pointRadius:0, borderWidth:0 });
  });

  // Disruption markers
  const events=(d.strategies[strats[0]].disruption_events||[])
    .filter(e=>e.event==='start'||e.event==='stochastic_start');
  if (events.length) {
    ds.push({ type:'scatter', label:'__b_dis',
      data:events.map(e=>({x:e.time_days,y:0})),
      pointStyle:'triangle', pointRadius:7, rotation:180,
      backgroundColor:'#dc2626', borderColor:'#dc2626', showLine:false });
  }

  C.inventory.data.labels=ts0.labels_days;
  C.inventory.data.datasets=ds;
  C.inventory.update();
}

// ── Source donut ──────────────────────────────────────────────────────────────
function updateSrc(d,st) {
  if (!d.strategies[st]) return;
  const mix=d.strategies[st].source_mix;
  const srcs=Object.keys(mix);
  const vals=srcs.map(s=>mix[s].barrels||0);
  const hasData=vals.some(v=>v>0);

  C.source.data.labels=srcs.map(s=>fmt(s).replace('Gulf Pipeline','Gulf Pipeline'));
  C.source.data.datasets[0].data=hasData?vals:srcs.map(()=>1);
  C.source.data.datasets[0].backgroundColor=srcs.map(s=>SRC_C[s]||'#99a0ae');
  C.source.data.datasets[0].borderColor=hasData?'#fff':srcs.map(()=>'#f0f1f3');
  C.source.update();
}

// ── Table ─────────────────────────────────────────────────────────────────────
function renderTable(d,strats) {
  const kArr=strats.map(s=>d.strategies[s].kpis);
  const bShort=Math.min(...kArr.map(k=>k.mean_shortage_hours));
  const bCost =Math.min(...kArr.map(k=>k.mean_avg_cost_per_bbl));
  const bDFR  =Math.max(...kArr.map(k=>k.mean_fulfillment_rate));
  const bTot  =Math.min(...kArr.map(k=>k.mean_total_cost));

  $('cmp-body').innerHTML=strats.map(st=>{
    const k=d.strategies[st].kpis;
    const b=(val,best,fn=v=>v,lower=true)=>{
      const isBest=lower?val===best:val===best;
      return isBest?`<td class="best">${fn(val)}</td>`:`<td>${fn(val)}</td>`;
    };
    const fd=k.first_shortage_hour?`Day ${Math.floor(k.first_shortage_hour/24)}`:'—';
    return `<tr>
      <td><span class="badge" style="background:${sc(st)}">${fmtS(st)}</span></td>
      ${b(k.mean_shortage_hours,bShort,v=>Math.round(v).toLocaleString())}
      <td>${Math.round(k.std_shortage_hours||0).toLocaleString()}</td>
      ${b(k.mean_total_cost,bTot,v=>`$${(v/1e9).toFixed(2)}B`)}
      ${b(k.mean_avg_cost_per_bbl,bCost,v=>`$${v.toFixed(2)}`)}
      ${b(k.mean_fulfillment_rate,bDFR,v=>`${(v*100).toFixed(1)}%`,false)}
      <td>${(k.mean_fleet_utilization*100).toFixed(1)}%</td>
      <td>${fd}</td>
    </tr>`;
  }).join('');
}

// ── Util ──────────────────────────────────────────────────────────────────────
const $=id=>document.getElementById(id);

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',async()=>{
  const r=await fetch('/api/meta');
  S.meta=await r.json();
  renderSidebar();
  attachListeners();
  initCharts();
});
