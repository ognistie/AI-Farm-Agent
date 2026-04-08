const S={c:false,r:false,s:{dryRun:false,genReport:true},tasks:0,xp:0};
let sk;

// Starfield
function initStars(){
    const c=document.getElementById('stars');if(!c)return;
    const ctx=c.getContext('2d');
    let w=c.width=window.innerWidth,h=c.height=window.innerHeight;
    const stars=Array.from({length:120},()=>({x:Math.random()*w,y:Math.random()*h,s:Math.random()*1.5+.3,sp:Math.random()*.15+.02}));
    function draw(){
        ctx.fillStyle='rgba(5,6,10,.15)';ctx.fillRect(0,0,w,h);
        stars.forEach(s=>{
            s.y+=s.sp;if(s.y>h){s.y=0;s.x=Math.random()*w}
            ctx.fillStyle=`rgba(0,255,200,${s.s/2})`;
            ctx.fillRect(Math.floor(s.x),Math.floor(s.y),Math.ceil(s.s),Math.ceil(s.s));
        });
        requestAnimationFrame(draw);
    }
    draw();
    window.addEventListener('resize',()=>{w=c.width=window.innerWidth;h=c.height=window.innerHeight});
}

function init(){
    initStars();
    sk=io();
    sk.on("connect",()=>{S.c=true;dot("ok");lg("info","SYSTEM ONLINE")});
    sk.on("disconnect",()=>{S.c=false;dot("off");lg("err","CONNECTION LOST")});
    sk.on("status",d=>lg("info",d.msg));
    sk.on("phase",d=>{lbl(d.msg.toUpperCase());lg("info",d.msg)});
    sk.on("plan_ready",d=>{renderPlan(d.plan);lg("ok","PLAN: "+d.plan.steps.length+" steps")});
    sk.on("step_start",d=>{prog(d.progress);hlP(d.step);addFc(d);lg("info","["+d.step+"/"+d.total+"] "+d.desc);lbl("STEP "+d.step+"/"+d.total);ldot(true);tab("feed")});
    sk.on("step_done",d=>{prog(d.progress);doneFc(d);dnP(d.step);lg(d.ok?"ok":"err",(d.ok?"✓ ":"✗ ")+d.result)});
    sk.on("task_done",d=>{S.r=false;btn(0);dot("ok");prog(100);ldot(0);lbl("COMPLETE");lg("ok","TASK COMPLETE");S.tasks++;$("tasks-n").textContent=S.tasks;$("qas").style.display="flex";$("btn-stop").style.display="none";if(d.skills&&d.skills.length)showSk(d.skills)});
    sk.on("cancelled",d=>{S.r=false;btn(0);dot("ok");ldot(0);lg("info","ABORTED");$("qas").style.display="flex";$("btn-stop").style.display="none"});
    sk.on("report_ready",d=>{renderRpt(d.report);tab("report");lg("ok","REPORT READY");if(d.report&&d.report.xp_earned){S.xp+=d.report.xp_earned}});
    sk.on("error",d=>{S.r=false;btn(0);dot("off");ldot(0);lbl("ERROR");lg("err",d.msg);$("qas").style.display="flex";$("btn-stop").style.display="none"});
    sk.on("api_usage",d=>{
        $("api-calls").textContent=d.calls||0;
        const tok=d.tokens_est||0;
        $("api-tokens").textContent=(tok/1000).toFixed(1)+"k";
        // Estimativa de custo: Haiku ~$0.25/1M input + $1.25/1M output, Sonnet ~$3/1M + $15/1M
        // Média ponderada simplificada: ~$2/1M tokens
        const cost=(tok/1000000)*2;
        $("api-cost").textContent="$"+cost.toFixed(3);
    });
    $("task-input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();go()}});
    document.querySelectorAll(".ptab").forEach(t=>t.addEventListener("click",()=>tab(t.dataset.tab)));
}

function go(){
    const v=$("task-input").value.trim();if(!v||S.r)return;
    S.r=true;clr("feed");clr("plan-box");clr("rpt");prog(0);btn(1);dot("work");ldot(1);lbl("PLANNING...");
    $("plan-section").style.display="none";$("qas").style.display="none";$("btn-stop").style.display="inline-flex";
    lg("info","► "+v);
    sk.emit("execute_task",{task:v,dry_run:S.s.dryRun,generate_report:S.s.genReport});
}

function forceStop(){sk.emit("force_stop");S.r=false;btn(0);dot("ok");ldot(0);lbl("HALTED");$("btn-stop").style.display="none";$("qas").style.display="flex";lg("err","■ EXECUTION HALTED")}

// PLAN
function renderPlan(p){
    const c=$("plan-box");c.innerHTML="";$("plan-section").style.display="block";
    p.steps.forEach(s=>{const d=mk("div","pi");d.id="pi-"+s.step;
        d.innerHTML='<span style="color:var(--amber)">'+s.step+'.</span> '+s.description+' <span style="color:var(--t3)">['+s.action+']</span>';
        c.appendChild(d)});
}
function hlP(n){document.querySelectorAll(".pi").forEach(e=>e.classList.remove("cur"));const e=$("pi-"+n);if(e){e.classList.add("cur");e.scrollIntoView({behavior:"smooth",block:"nearest"})}}
function dnP(n){const e=$("pi-"+n);if(e){e.classList.remove("cur");e.classList.add("dn")}}

// FEED
function addFc(d){
    const f=$("feed");const em=f.querySelector(".feed-empty");if(em)em.remove();
    const c=mk("div","fc active");c.id="fc-"+d.step;
    c.innerHTML='<div class="fc-h"><span class="fc-n">'+d.step+'</span><span class="fc-t">'+d.action+'</span></div><div class="fc-b"><div class="fc-d">'+d.desc+'</div><div class="fc-r">⏳ EXECUTING...</div></div>';
    f.appendChild(c);c.scrollIntoView({behavior:"smooth",block:"nearest"});
}
function doneFc(d){
    const c=$("fc-"+d.step);if(!c)return;
    c.className="fc "+(d.ok?"done":"fail");
    c.querySelector(".fc-r").textContent=d.result||"OK";
    if(d.screenshot){const im=mk("div","fc-i");im.innerHTML='<img src="/captures/'+d.screenshot+'" loading="lazy">';im.onclick=()=>window.open("/captures/"+d.screenshot,"_blank");c.appendChild(im)}
}
function showSk(s){
    const c=mk("div","sk");c.innerHTML='<div class="sk-l">★ SKILLS UNLOCKED ★</div><div class="sk-tags">'+s.map(x=>'<span class="sk-tag">'+x.toUpperCase()+'</span>').join("")+'</div>';
    $("feed").appendChild(c);c.scrollIntoView({behavior:"smooth"});
}

// REPORT
function renderRpt(r){
    const c=$("rpt");c.innerHTML="";
    if(!r||r.error){c.innerHTML='<div style="color:var(--red);padding:20px;font-family:var(--mono)">'+(r?r.message:'No data')+'</div>';return}
    // Summary
    const sum=mk("div","rp");
    sum.innerHTML='<h4>◆ MISSION SUMMARY</h4><p>'+(r.summary||r.titulo||"")+'</p><div class="xp">+'+(r.xp_earned||r.pontuacao_execucao||0)+' XP</div>';
    if(r.skills||r.habilidades_demonstradas){
        const tags=(r.skills||[]).concat((r.habilidades_demonstradas||[]).map(h=>h.nome||h));
        sum.innerHTML+='<div class="sk-tags" style="margin-top:8px">'+tags.map(x=>'<span class="sk-tag">'+x.toUpperCase()+'</span>').join("")+'</div>';
    }
    c.appendChild(sum);
    // Steps
    (r.steps||[]).forEach(s=>{
        const d=mk("div","rs");
        d.innerHTML='<div style="font-size:11px;color:var(--t1)">'+(s.what||s.titulo||"")+'</div><div class="con">'+(s.concept||s.nome||"")+'</div><div class="ins">'+(s.insight||s.descricao||"")+'</div>';
        c.appendChild(d)});
    // Next
    const next=r.next_level||r.proximos_passos_sugeridos;
    if(next){const n=mk("div","rn");n.innerHTML='<b>► NEXT:</b> '+(Array.isArray(next)?next.join(" | "):next);c.appendChild(n)}
}

// LOG
function lg(t,m){
    const ts=new Date().toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    const d=mk("div","lg "+t);d.innerHTML='<span class="ts">['+ts+']</span> <span class="ms">'+m+'</span>';
    const logs=$("logs");logs.appendChild(d);logs.scrollTop=logs.scrollHeight;
}

// UI
function dot(s){const d=$("dot");d.className="led";if(s==="off")d.classList.add("off");if(s==="work")d.classList.add("work")}
function ldot(on){const d=$("live-dot");if(d)d.style.boxShadow=on?"0 0 10px var(--green),0 0 3px var(--green)":"0 0 4px var(--green)"}
function lbl(t){$("live-label").textContent=t;$("status-txt").textContent=t}
function prog(p){$("prog").style.width=p+"%"}
function btn(on){const b=$("btn");if(on){b.querySelector(".exec-text").textContent="RUNNING...";b.classList.add("running");b.disabled=true}else{b.querySelector(".exec-text").textContent="EXECUTAR";b.classList.remove("running");b.disabled=false}}
function tab(n){document.querySelectorAll(".ptab").forEach(t=>t.classList.toggle("active",t.dataset.tab===n));document.querySelectorAll(".tab-pane").forEach(p=>p.classList.toggle("active",p.id==="tp-"+n))}
function clr(id){const e=$(id);if(e)e.innerHTML=""}
function setEx(t){$("task-input").value=t;$("task-input").focus()}
function $(id){return document.getElementById(id)}
function mk(t,c){const e=document.createElement(t);if(c)e.className=c;return e}

document.addEventListener("DOMContentLoaded",()=>{init();lg("info","AI FARM AGENT v9 — READY")});