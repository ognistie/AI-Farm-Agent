/* ══════════════════════════════════════ */
/* AI Farm Agent v2.0 — Frontend        */
/* ══════════════════════════════════════ */

const S = { c: false, r: false, s: { dryRun: false, genReport: true }, tasks: 0, xp: 0 };
let sk;

const hologramData = {
    'autonomous': "CORE DIRECTIVE // AUTONOMOUS MODE",
    'computer': "SYSTEM LINK // HARDWARE INTERFACE",
    'operator': "HUMAN PROXY // MANUAL OVERRIDE"
};

/* ═══ MATRIX ENGINE V2 (MULTIDIRECIONAL + HOLOGRAMA ROSTO) ═══ */
function initMatrixEngine() {
    const c = document.getElementById('rain-canvas');
    if (!c) return;
    const ctx = c.getContext('2d');
    c.width = window.innerWidth;
    c.height = window.innerHeight;

    const chars = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEF';
    const fontSize = 14;
    const cols = Math.floor(c.width / fontSize);
    const rows = Math.floor(c.height / fontSize);

    // Sistema de cascata que anda em múltiplas direções
    class Stream {
        constructor() { this.reset(); }
        reset() {
            let dir = Math.random();
            if (dir < 0.7) { this.vx = 0; this.vy = 1; this.x = Math.floor(Math.random() * cols); this.y = -Math.floor(Math.random() * 50); }
            else if (dir < 0.8) { this.vx = 0; this.vy = -1; this.x = Math.floor(Math.random() * cols); this.y = rows + Math.floor(Math.random() * 50); }
            else if (dir < 0.9) { this.vx = 1; this.vy = 0; this.x = -Math.floor(Math.random() * 50); this.y = Math.floor(Math.random() * rows); }
            else { this.vx = -1; this.vy = 0; this.x = cols + Math.floor(Math.random() * 50); this.y = Math.floor(Math.random() * rows); }
            
            this.speed = Math.floor(Math.random() * 2) + 1;
            this.chars = [];
            this.length = Math.floor(Math.random() * 15) + 5;
        }
        update() {
            this.x += this.vx * this.speed;
            this.y += this.vy * this.speed;
            this.chars.unshift({ x: this.x, y: this.y, char: chars[Math.floor(Math.random() * chars.length)] });
            if (this.chars.length > this.length) this.chars.pop();

            if ((this.vy > 0 && this.y > rows + this.length) || (this.vy < 0 && this.y < -this.length) || 
                (this.vx > 0 && this.x > cols + this.length) || (this.vx < 0 && this.x < -this.length)) {
                this.reset();
            }
        }
    }

    const streams = Array.from({length: 150}, () => new Stream());
    let mouseX = -1000;
    let mouseY = -1000;
    document.addEventListener('mousemove', (e) => { mouseX = e.clientX; mouseY = e.clientY; });

    // Equação para desenhar o "rosto de código" (estilo da foto_45b7fb)
    function getFaceIntensity(gx, gy) {
        const cx = Math.floor(cols * 0.20); 
        const cy = Math.floor(rows * 0.5);
        const rx = Math.floor(cols * 0.12);
        const ry = Math.floor(rows * 0.35);

        let dy = gy - cy;
        let adjustedRx = rx;

        // Afina um pouco embaixo (formato de crânio)
        if (dy > 0) {
            adjustedRx = rx * (1 - (dy / ry) * 0.4);
        }

        const distSq = Math.pow(gx - cx, 2) / Math.pow(adjustedRx, 2) + Math.pow(dy, 2) / Math.pow(ry, 2);

        if (distSq <= 1) {
            // Buracos dos olhos
            const eyeY = cy - Math.floor(ry * 0.1);
            const leftEyeX = cx - Math.floor(rx * 0.4);
            const rightEyeX = cx + Math.floor(rx * 0.4);
            const eyeR = rx * 0.25;

            if (Math.hypot(gx - leftEyeX, gy - eyeY) < eyeR || Math.hypot(gx - rightEyeX, gy - eyeY) < eyeR) {
                return 0.1; // Fundo do olho escuro
            }

            // Sombreamento base (Rosto brilhante no centro)
            return 0.9 - (distSq * 0.4);
        }
        return 0;
    }

    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.font = fontSize + 'px monospace';

        // 1. Drenagem do código multidirecional (Rastro interativo do mouse)
        streams.forEach(s => {
            s.update();
            s.chars.forEach((cObj, i) => {
                let px = cObj.x * fontSize;
                let py = cObj.y * fontSize;
                
                const mouseDist = Math.hypot(px - mouseX, py - mouseY);
                if (mouseDist < 80) {
                    ctx.fillStyle = '#ffffff';
                    // Efeito do código se quebrando e fugindo do mouse
                    const angle = Math.atan2(py - mouseY, px - mouseX);
                    px += Math.cos(angle) * 10;
                    py += Math.sin(angle) * 10;
                    ctx.fillText(chars[Math.floor(Math.random() * chars.length)], px, py);
                } else {
                    const alpha = 1 - (i / s.length);
                    ctx.fillStyle = (i === 0) ? '#ffffff' : `rgba(0, 255, 65, ${alpha})`;
                    ctx.fillText(cObj.char, px, py);
                }
            });
        });

        // 2. Projeta a face da Matrix no lado esquerdo
        for (let gx = 0; gx < cols * 0.4; gx++) {
            for (let gy = 0; gy < rows; gy++) {
                const intensity = getFaceIntensity(gx, gy);
                if (intensity > 0 && Math.random() > 0.8) {
                    const px = gx * fontSize;
                    const py = gy * fontSize;
                    const char = chars[Math.floor(Math.random() * chars.length)];
                    
                    if (Math.hypot(px - mouseX, py - mouseY) < 150) {
                        ctx.fillStyle = '#ffffff';
                        ctx.shadowBlur = 10;
                        ctx.shadowColor = '#ffffff';
                    } else {
                        ctx.fillStyle = `rgba(0, 255, 65, ${intensity})`;
                        ctx.shadowBlur = 0;
                    }
                    ctx.fillText(char, px, py);
                    ctx.shadowBlur = 0; 
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();

    window.addEventListener('resize', () => {
        c.width = window.innerWidth;
        c.height = window.innerHeight;
    });
}

/* ═══ HOVER HUD DATA PROFILE DAS PALAVRAS ═══ */
function initHoverReveal() {
    const hoverElements = document.querySelectorAll('.matrix-hover');
    const revealContainer = document.getElementById('hover-reveal-container');
    const revealBg = document.getElementById('hover-reveal-bg'); 
    const hologramDesc = document.getElementById('hologram-desc');

    if (!revealContainer || !revealBg || hoverElements.length === 0) return;

    hoverElements.forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const imgSrc = el.getAttribute('data-image');
            if(imgSrc) {
                revealBg.style.backgroundImage = `url('${imgSrc}')`;
            } else {
                revealBg.style.backgroundImage = 'none';
            }
            
            const dataKey = el.textContent.trim().toLowerCase();
            hologramDesc.textContent = hologramData[dataKey] || "NEURAL LINK // DATA FEED ACTIVE";
            
            revealContainer.style.opacity = '1';
            revealContainer.classList.add('glitch-anim');
            setTimeout(() => revealContainer.classList.remove('glitch-anim'), 300);
        });

        el.addEventListener('mousemove', (e) => {
            const x = e.clientX + 30;
            const y = e.clientY + 30;
            revealContainer.style.transform = `translate(${x}px, ${y}px) scale(1) skew(0deg)`;
        });

        el.addEventListener('mouseleave', (e) => {
            revealContainer.style.opacity = '0';
            const x = e.clientX + 30;
            const y = e.clientY + 30;
            revealContainer.style.transform = `translate(${x}px, ${y}px) scale(0.8) skew(10deg)`;
        });
    });
}

/* ═══ MANTIDO 100% INTACTO: SUAS FUNÇÕES ORIGINAIS DO APP.JS ═══ */
function enterMatrix() {
    const splashContent = document.querySelector('.splash-content');
    const overlay = document.getElementById('transition-overlay');
    const transText = document.getElementById('transition-text');
    
    splashContent.style.opacity = '0';
    splashContent.style.transition = 'opacity 0.5s';

    setTimeout(() => {
        overlay.classList.remove('hidden');
        overlay.classList.add('active');
        transText.textContent = "QUEBRANDO PROTOCOLOS...";
        transText.style.color = "#ff1744"; 
        transText.style.textShadow = "0 0 20px #ff1744";
    }, 500);

    setTimeout(() => {
        transText.textContent = "ENTRANDO NA MATRIX";
        transText.style.color = "#fff";
        transText.style.textShadow = "0 0 30px #00ff41, 0 0 60px #00ff41";
    }, 2500);

    setTimeout(() => {
        overlay.classList.remove('active');
        document.getElementById('splash').style.display = 'none';
        
        const mainApp = document.getElementById('main-app');
        mainApp.style.display = 'flex';
        mainApp.style.flexDirection = 'column';
        mainApp.style.minHeight = '100vh';
        mainApp.style.opacity = '0';
        
        setTimeout(() => {
            mainApp.style.transition = 'opacity 1s ease-in';
            mainApp.style.opacity = '1';
        }, 100);
        
    }, 4500);
}

function rejectMatrix() {
    const splash = document.querySelector('.splash-content');
    splash.innerHTML = `
        <div style="font-family:var(--font-mono);color:#00e5ff;font-size:16px;animation:fadeInUp 0.5s ease; background: rgba(0,0,0,0.8); padding: 40px; border: 1px solid #00e5ff;">
            <p style="font-size:40px;margin-bottom:16px;text-shadow: 0 0 20px #00e5ff;">🔵</p>
            <p style="letter-spacing: 2px;">DESCONEXÃO INICIADA.</p>
            <p style="margin-top:16px;color:#0088aa;font-size:14px; font-style: italic;">"A história acaba. Você acorda na sua cama e acredita no que quiser."</p>
            <button onclick="location.reload()" style="margin-top:32px;padding:12px 32px;border:1px solid #00e5ff;background:transparent;color:#00e5ff;cursor:pointer;font-family:var(--font-display);font-size:14px; letter-spacing:2px; transition: 0.3s;" onmouseover="this.style.background='rgba(0,229,255,0.2)'" onmouseout="this.style.background='transparent'">REINICIAR SIMULAÇÃO</button>
        </div>`;
}

function switchView(name) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    const view = document.getElementById('view-' + name);
    if (view) view.classList.add('active');
    const tab = document.querySelector('.nav-tab[data-view="' + name + '"]');
    if (tab) tab.classList.add('active');
}

function initSocket() {
    sk = io('http://127.0.0.1:5000', {
        query: { token: '17qXMKndUUepc2Z_PQe7dzLVRuuWR0n3tGCT2ukDb0E' } 
    });

    sk.on('connect', () => { S.c = true; dot('ok'); lg('info', 'SYSTEM ONLINE'); });
    sk.on('disconnect', () => { S.c = false; dot('off'); lg('err', 'CONNECTION LOST'); });
    sk.on('status', d => lg('info', d.msg));
    sk.on('phase', d => { lbl(d.msg.toUpperCase()); lg('info', d.msg); });
    sk.on('plan_ready', d => { renderPlan(d.plan); lg('ok', 'PLAN: ' + d.plan.steps.length + ' steps'); });
    sk.on('step_start', d => {
        prog(d.progress); hlP(d.step); addFc(d);
        lg('info', '[' + d.step + '/' + d.total + '] ' + d.desc);
        lbl('STEP ' + d.step + '/' + d.total);
        ldot(true); tab('feed');
    });
    sk.on('step_done', d => {
        prog(d.progress); doneFc(d); dnP(d.step);
        lg(d.ok ? 'ok' : 'err', (d.ok ? '✓ ' : '✗ ') + d.result);
    });
    sk.on('task_done', d => {
        S.r = false; btn(0); dot('ok'); prog(100); ldot(0); lbl('COMPLETE');
        lg('ok', 'TASK COMPLETE'); S.tasks++;
        $('tasks-n').textContent = S.tasks;
        $('qas').style.display = 'flex';
        $('btn-stop').style.display = 'none';
        if (d.skills && d.skills.length) showSk(d.skills);
    });
    sk.on('cancelled', d => {
        S.r = false; btn(0); dot('ok'); ldot(0); lg('info', 'ABORTED');
        $('qas').style.display = 'flex'; $('btn-stop').style.display = 'none';
    });
    sk.on('report_ready', d => {
        renderRpt(d.report); tab('report'); lg('ok', 'REPORT READY');
        if (d.report && d.report.xp_earned) S.xp += d.report.xp_earned;
    });
    sk.on('error', d => {
        S.r = false; btn(0); dot('off'); ldot(0); lbl('ERROR');
        lg('err', d.msg); $('qas').style.display = 'flex'; $('btn-stop').style.display = 'none';
    });
    sk.on('api_usage', d => {
        $('api-calls').textContent = d.calls || 0;
        const tok = d.tokens_est || 0;
        $('api-tokens').textContent = (tok / 1000).toFixed(1) + 'k';
        const cost = (tok / 1000000) * 2;
        $('api-cost').textContent = '$' + cost.toFixed(3);
    });
}

function go() {
    const v = $('task-input').value.trim();
    if (!v || S.r) return;
    S.r = true;
    clr('feed'); clr('plan-box'); clr('rpt'); prog(0);
    btn(1); dot('work'); ldot(1); lbl('PLANNING...');
    $('plan-section').style.display = 'none';
    $('qas').style.display = 'none';
    $('btn-stop').style.display = 'inline-flex';
    lg('info', '► ' + v);
    sk.emit('execute_task', { task: v, dry_run: S.s.dryRun, generate_report: S.s.genReport });
}

function forceStop() {
    sk.emit('force_stop'); S.r = false;
    btn(0); dot('ok'); ldot(0); lbl('HALTED');
    $('btn-stop').style.display = 'none';
    $('qas').style.display = 'flex';
    lg('err', '■ EXECUTION HALTED');
}

function renderPlan(p) {
    const c = $('plan-box'); c.innerHTML = '';
    $('plan-section').style.display = 'block';
    p.steps.forEach(s => {
        const d = mk('div', 'pi'); d.id = 'pi-' + s.step;
        d.innerHTML = '<span style="color:var(--amber)">' + s.step + '.</span> ' + s.description + ' <span style="color:var(--t3)">[' + s.action + ']</span>';
        c.appendChild(d);
    });
}
function hlP(n) { document.querySelectorAll('.pi').forEach(e => e.classList.remove('cur')); const e = $('pi-' + n); if (e) { e.classList.add('cur'); e.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } }
function dnP(n) { const e = $('pi-' + n); if (e) { e.classList.remove('cur'); e.classList.add('dn'); } }

function addFc(d) {
    const f = $('feed'); const em = f.querySelector('.feed-empty'); if (em) em.remove();
    const c = mk('div', 'fc active'); c.id = 'fc-' + d.step;
    c.innerHTML = '<div class="fc-h"><span class="fc-n">' + d.step + '</span><span class="fc-t">' + d.action + '</span></div><div class="fc-b"><div class="fc-d">' + d.desc + '</div><div class="fc-r">⏳ Executando...</div></div>';
    f.appendChild(c); c.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function doneFc(d) {
    const c = $('fc-' + d.step); if (!c) return;
    c.className = 'fc ' + (d.ok ? 'done' : 'fail');
    c.querySelector('.fc-r').textContent = d.result || 'OK';
    if (d.screenshot) {
        const im = mk('div', 'fc-i');
        im.innerHTML = '<img src="/captures/' + d.screenshot + '" loading="lazy">';
        im.onclick = () => window.open('/captures/' + d.screenshot, '_blank');
        c.appendChild(im);
    }
}
function showSk(s) {
    const c = mk('div', 'sk');
    c.innerHTML = '<div class="sk-l">★ SKILLS UNLOCKED ★</div><div class="sk-tags">' + s.map(x => '<span class="sk-tag">' + x.toUpperCase() + '</span>').join('') + '</div>';
    $('feed').appendChild(c); c.scrollIntoView({ behavior: 'smooth' });
}

function renderRpt(r) {
    const c = $('rpt'); c.innerHTML = '';
    if (!r || r.error) { c.innerHTML = '<div style="color:var(--red);padding:20px">' + (r ? r.message : 'No data') + '</div>'; return; }
    const sum = mk('div', 'rp');
    sum.innerHTML = '<h4>◆ MISSION SUMMARY</h4><p>' + (r.summary || r.titulo || '') + '</p><div class="xp">+' + (r.xp_earned || r.pontuacao_execucao || 0) + ' XP</div>';
    if (r.skills || r.habilidades_demonstradas) {
        const tags = (r.skills || []).concat((r.habilidades_demonstradas || []).map(h => h.nome || h));
        sum.innerHTML += '<div class="sk-tags" style="margin-top:8px">' + tags.map(x => '<span class="sk-tag">' + x.toUpperCase() + '</span>').join('') + '</div>';
    }
    c.appendChild(sum);
    (r.steps || []).forEach(s => {
        const d = mk('div', 'rs');
        d.innerHTML = '<div style="font-size:13px;color:var(--t1)">' + (s.what || s.titulo || '') + '</div><div class="con">' + (s.concept || s.nome || '') + '</div><div class="ins">' + (s.insight || s.descricao || '') + '</div>';
        c.appendChild(d);
    });
    const next = r.next_level || r.proximos_passos_sugeridos;
    if (next) {
        const n = mk('div', 'rn');
        n.innerHTML = '<b>► NEXT:</b> ' + (Array.isArray(next) ? next.join(' | ') : next);
        c.appendChild(n);
    }
}

function lg(t, m) {
    const ts = new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const d = mk('div', 'lg ' + t);
    d.innerHTML = '<span class="ts">[' + ts + ']</span> <span class="ms">' + m + '</span>';
    const logs = $('logs'); logs.appendChild(d); logs.scrollTop = logs.scrollHeight;
}

function dot(s) { const d = $('dot'); d.className = 'status-led'; if (s === 'off') d.classList.add('off'); if (s === 'work') d.classList.add('work'); }
function ldot(on) { const d = $('live-dot'); if (d) d.style.boxShadow = on ? '0 0 12px var(--green)' : '0 0 4px var(--green)'; }
function lbl(t) { $('live-label').textContent = t; $('status-txt').textContent = t; }
function prog(p) { $('prog').style.width = p + '%'; }
function btn(on) {
    const b = $('btn');
    if (on) { b.querySelector('.exec-text').textContent = 'EXECUTANDO...'; b.classList.add('running'); b.disabled = true; }
    else { b.querySelector('.exec-text').textContent = 'EXECUTAR'; b.classList.remove('running'); b.disabled = false; }
}
function tab(n) {
    document.querySelectorAll('.ltab').forEach(t => t.classList.toggle('active', t.dataset.tab === n));
    document.querySelectorAll('.tab-content').forEach(p => p.classList.toggle('active', p.id === 'tp-' + n));
}
function clr(id) { const e = $(id); if (e) e.innerHTML = ''; }
function setEx(t) { $('task-input').value = t; $('task-input').focus(); }
function $(id) { return document.getElementById(id); }
function mk(t, c) { const e = document.createElement(t); if (c) e.className = c; return e; }

/* ═══ INICIALIZAÇÃO GERAL ═══ */
document.addEventListener('DOMContentLoaded', () => {
    initMatrixEngine(); // Liga a Cascata que interage com o mouse + Holograma
    initHoverReveal();  // Liga o HUD nas palavras
    initSocket();
    
    $('task-input').addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(); }
    });
    lg('info', 'AI FARM AGENT v2.0 — READY');
});