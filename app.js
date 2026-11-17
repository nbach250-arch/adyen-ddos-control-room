'use strict';
let current = null, busy = false;
const $ = id => document.getElementById(id);
const fmt = n => Math.round(n || 0).toLocaleString('en-US');
const money = n => '$' + Number(n || 0).toFixed(2);
async function api(path, body){
 const opts = body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {};
 const r = await fetch(path,opts); const data = await r.json(); if(!r.ok)throw new Error(data.error || 'Request failed');return data;
}
function toast(msg){$('toast').textContent=msg;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),2700)}
async function send(body){try{current=await api('/api/action',body);render(current);}catch(e){toast('Error: '+e.message)}}
function providerCard(p, active){return `<div class="provider-card ${active?'selected':''} ${!p.healthy?'bad':''}"><div class="provider-top"><strong>🛡 Shield ${p.id}</strong><span class="tag ${!p.healthy?'bad':''}">${p.healthy?'HEALTHY':'DEGRADED'}</span></div><div class="metric-row"><span>Latency</span><b>${p.latency} ms</b></div><div class="metric-row"><span>Errors</span><b>${p.errors}%</b></div><div class="metric-row"><span>Used capacity</span><b>${p.utilization}%</b></div><div class="meter"><span class="${p.utilization>85?'hot':''}" style="width:${Math.min(100,p.utilization)}%"></span></div><button class="routebtn" data-route="${p.id}" ${active?'disabled':''}>${active?'● ACTIVE ROUTE':'⇢ Route here'}</button></div>`}
function render(s){
 if(!s)return;
 const total=s.total_success+s.total_failed; const rate=total?100*s.total_success/total:100;
 $('successRate').textContent=rate.toFixed(1)+'%';$('successRate').style.color=rate>=99?'#46e6ac':'#ff8496';
 $('paid').textContent=fmt(s.total_success);$('failed').textContent=fmt(s.total_failed);$('cost').textContent=money(s.total_cost);
 $('activePill').textContent='ACTIVE: SHIELD '+s.active;
 $('trafficIn').textContent=fmt(s.legitimate)+' legitimate req/s';
 $('attackIn').textContent=fmt(s.last.attack)+' attack req/s';
 $('paymentIn').textContent=fmt(s.last.successful)+' successful req/s';
 $('paymentFailed').textContent=fmt(s.last.failed)+' failed req/s';
 $('blockedText').textContent=fmt(s.last.blocked)+' attack requests blocked this tick';
 const chosen=(s.providers||{})[s.active];
 $('routingText').textContent=chosen?(chosen.healthy?'Current route healthy':'Current route under stress ('+s.fail_streak+'/3 failed checks)'):'Preparing telemetry';
 $('routingText').style.color=chosen&&!chosen.healthy?'#ff8496':'#abdec8';
 ['A','B','C'].forEach(id=>{let el=$('flow'+id),p=s.providers[id]; el.className='tiny-flow'+(s.active===id?' selected':'')+(p&&!p.healthy?' unhealthy':'');});
 $('providerGrid').innerHTML=['A','B','C'].map(id=>providerCard(s.providers[id],s.active===id)).join('');
 document.querySelectorAll('[data-route]').forEach(el=>el.addEventListener('click',()=>send({command:'route',provider:el.dataset.route})));
 $('events').innerHTML=s.events.map(e=>`<div class="event ${e.type}"><div class="when">TICK ${e.tick}</div><div class="message">${escapeHtml(e.message)}</div></div>`).join('');
 $('switchCount').textContent=s.switches+' SWITCH'+(s.switches===1?'':'ES');$('tickText').textContent='TICK '+s.tick;
 $('attackStatus').textContent=s.scenario==='none'?'No active attack. Pick a scenario to begin.':'⚠ '+s.scenarios[s.scenario]+' targeting Shield '+s.target+' — intensity '+s.intensity+'%';
 $('pauseBtn').textContent=s.pause?'▶ Resume':'⏸ Pause';
 $('auto').checked=s.auto;
 drawChart(s.history); 
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function drawChart(points){
 const c=$('chart'), dpr=window.devicePixelRatio||1, w=c.clientWidth, h=184;
 if(!w)return;
 c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);
 const ctx=c.getContext('2d');ctx.scale(dpr,dpr);ctx.clearRect(0,0,w,h);
 const pad={left:35,right:10,top:12,bottom:21},cw=w-pad.left-pad.right,ch=h-pad.top-pad.bottom;
 const max=Math.max(800,...points.map(p=>p.success+p.failed))*1.12;
 ctx.strokeStyle='#2b4056';ctx.lineWidth=1;ctx.font='10px system-ui';ctx.fillStyle='#849bb2';
 for(let i=0;i<=4;i++){const y=pad.top+ch*i/4;ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(w-pad.right,y);ctx.stroke();ctx.fillText(fmt(max*(4-i)/4),0,y+3)}
 if(points.length<1)return;
 const x=i=>pad.left+(points.length===1?cw/2:i*cw/(points.length-1));
 for(const [field,color] of [['success','#38d6a0'],['failed','#ff7189']]){
   ctx.strokeStyle=color;ctx.lineWidth=2.7;ctx.lineJoin='round';ctx.beginPath();
   points.forEach((p,i)=>{const y=pad.top+ch*(1-p[field]/max);if(i===0)ctx.moveTo(x(i),y);else ctx.lineTo(x(i),y)});ctx.stroke();
   const last=points[points.length-1];ctx.fillStyle=color;ctx.beginPath();ctx.arc(x(points.length-1),pad.top+ch*(1-last[field]/max),3.5,0,Math.PI*2);ctx.fill();
 }
}
function bindSlider(id,fmtValue,cmd){
 const el=$(id), label=$(id+'Val');
 el.addEventListener('input',()=>label.textContent=fmtValue(el.value));
 if(cmd){el.addEventListener('change',()=>send({command:'settings',[id]:Number(el.value)}));}
}
bindSlider('intensity',v=>v+'%',false);bindSlider('filter',v=>v+'%',true);bindSlider('reserve',v=>v+'%',true);bindSlider('legitimate',v=>v+' req/s',true);
$('auto').addEventListener('change',()=>send({command:'settings',auto:$('auto').checked}));
$('attackBtn').addEventListener('click',async()=>{await send({command:'settings',intensity:Number($('intensity').value)});await send({command:'attack',scenario:$('scenario').value,target:$('target').value});toast('Simulated attack launched. Watch the failover!')});
$('stopBtn').addEventListener('click',()=>send({command:'stop_attack'}));
$('resetBtn').addEventListener('click',()=>{if(confirm('Reset all simulated results and incident history?'))send({command:'reset'})});
$('pauseBtn').addEventListener('click',()=>send({command:'settings',pause:!current.pause}));
$('stepBtn').addEventListener('click',()=>send({command:'step'}));
window.addEventListener('resize',()=>current&&drawChart(current.history));
async function loop(){if(busy)return;busy=true;try{current=await api('/api/tick',{});render(current)}catch(e){console.error(e)}finally{busy=false}}
(async()=>{try{current=await api('/api/state');render(current)}catch(e){toast('Could not connect to Flask server')}setInterval(loop,2000)})();
