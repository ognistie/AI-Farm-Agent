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

    // ═══ GLOBO TERRESTRE 3D — Geografia real, Brasil destacado ═══
    const landMasses = [
        // ── AMÉRICA DO NORTE ──
        // Canadá
        [-2.45,-1.05, 0.82, 1.22], [-2.6,-2.0, 0.95, 1.18], [-1.6,-1.05, 0.75, 0.95],
        [-2.3,-1.8, 1.05, 1.2], [-2.8,-2.4, 0.95, 1.1],
        // Alasca
        [-2.95,-2.55, 1.0, 1.18], [-3.1,-2.85, 0.95, 1.08],
        // EUA
        [-2.15,-1.25, 0.52, 0.85], [-2.05,-1.3, 0.58, 0.82], [-1.55,-1.28, 0.42, 0.58],
        [-2.15,-1.75, 0.52, 0.62], [-1.4,-1.25, 0.45, 0.55],
        // México
        [-1.95,-1.55, 0.32, 0.55], [-1.82,-1.6, 0.28, 0.42],
        // América Central
        [-1.58,-1.38, 0.15, 0.32], [-1.48,-1.35, 0.1, 0.22],
        // Cuba / Caribe
        [-1.48,-1.3, 0.35, 0.4], [-1.25,-1.12, 0.3, 0.35],

        // ── AMÉRICA DO SUL (exceto Brasil) ──
        // Venezuela / Colômbia
        [-1.32,-1.1, 0.0, 0.2], [-1.4,-1.2, 0.02, 0.12],
        // Peru / Equador
        [-1.42,-1.22, -0.25, 0.0], [-1.38,-1.28, -0.15, -0.02],
        // Bolívia
        [-1.2,-1.05, -0.3, -0.12],
        // Chile (fino e longo)
        [-1.28,-1.18, -0.95, -0.25], [-1.25,-1.18, -0.6, -0.3],
        // Argentina
        [-1.22,-1.02, -0.85, -0.28], [-1.18,-1.05, -0.55, -0.3],
        // Paraguai / Uruguai
        [-1.05,-0.92, -0.42, -0.28], [-0.98,-0.88, -0.58, -0.48],
        // Patagônia
        [-1.25,-1.1, -0.88, -0.78],

        // ── EUROPA ──
        // Ibéria
        [-0.18, 0.05, 0.62, 0.75], [-0.15, 0.02, 0.58, 0.65],
        // França
        [-0.08, 0.12, 0.72, 0.85], [0.0, 0.1, 0.68, 0.75],
        // Ilhas Britânicas
        [-0.1, 0.05, 0.85, 0.98], [-0.05, 0.0, 0.88, 0.95],
        // Itália
        [0.12, 0.28, 0.6, 0.78], [0.15, 0.22, 0.58, 0.65],
        // Alemanha / Polônia / Bálticos
        [0.08, 0.38, 0.82, 0.98], [0.15, 0.42, 0.85, 0.95],
        // Escandinávia
        [0.08, 0.28, 0.98, 1.2], [0.15, 0.35, 1.02, 1.15],
        // Bálcãs / Grécia
        [0.25, 0.45, 0.6, 0.78], [0.32, 0.42, 0.58, 0.65],
        // Turquia
        [0.45, 0.72, 0.62, 0.72],
        // Europa Oriental
        [0.35, 0.7, 0.78, 1.05], [0.5, 0.8, 0.85, 1.0],

        // ── RÚSSIA ──
        [0.5, 2.8, 0.9, 1.2], [0.7, 2.5, 0.95, 1.15], [1.0, 3.0, 0.85, 1.1],
        [2.2, 2.8, 0.78, 0.95],

        // ── ÁFRICA ──
        // Norte da África / Magreb
        [-0.2, 0.55, 0.35, 0.58], [0.0, 0.6, 0.38, 0.55],
        // África Ocidental
        [-0.3, 0.15, 0.08, 0.38], [-0.25, 0.1, 0.12, 0.3],
        // Congo / África Central
        [0.1, 0.52, -0.08, 0.15], [0.15, 0.48, -0.05, 0.1],
        // África Oriental
        [0.5, 0.72, -0.2, 0.2], [0.55, 0.7, -0.08, 0.15],
        // Corno da África
        [0.62, 0.88, 0.02, 0.2],
        // África do Sul
        [0.25, 0.55, -0.6, -0.2], [0.3, 0.52, -0.5, -0.25],
        // Madagascar
        [0.72, 0.82, -0.4, -0.2],

        // ── ORIENTE MÉDIO ──
        [0.6, 0.9, 0.35, 0.58], [0.72, 0.85, 0.38, 0.55],
        // Arábia
        [0.62, 0.88, 0.22, 0.42],

        // ── ÁSIA ──
        // Índia
        [1.1, 1.45, 0.12, 0.55], [1.15, 1.4, 0.05, 0.35], [1.2, 1.35, -0.02, 0.15],
        // Sri Lanka
        [1.35, 1.42, 0.05, 0.12],
        // Sudeste Asiático
        [1.5, 1.85, 0.02, 0.42], [1.6, 1.9, 0.15, 0.38],
        // China
        [1.3, 2.15, 0.45, 0.85], [1.5, 2.1, 0.5, 0.78], [1.7, 2.05, 0.55, 0.72],
        // Mongólia
        [1.5, 2.0, 0.75, 0.85],
        // Coreia
        [2.15, 2.28, 0.55, 0.68],
        // Japão
        [2.25, 2.5, 0.52, 0.78], [2.28, 2.45, 0.55, 0.72], [2.3, 2.42, 0.48, 0.58],
        // Indonésia
        [1.65, 2.35, -0.15, 0.08], [1.8, 2.1, -0.12, 0.02],

        // ── OCEANIA ──
        // Austrália
        [1.95, 2.65, -0.65, -0.18], [2.0, 2.55, -0.58, -0.22], [2.1, 2.5, -0.5, -0.25],
        // Nova Zelândia
        [2.85, 3.0, -0.72, -0.58], [2.88, 2.98, -0.62, -0.52],

        // ── GROENLÂNDIA ──
        [-0.9,-0.45, 1.05, 1.3], [-0.8,-0.5, 1.1, 1.25],
    ];

    // ── BRASIL (polígonos mais detalhados) ──
    const brazil = [
        [-1.28,-0.6, -0.58, 0.08],
        [-1.22,-0.65, -0.52, 0.05],
        [-1.15,-0.62, -0.45, 0.02],
        [-1.08,-0.6, -0.35, -0.02],
        [-1.0,-0.62, -0.28, -0.05],
        [-0.95,-0.6, -0.18, -0.08],
        [-1.3,-0.85, -0.55, -0.15],
        [-1.15,-0.72, -0.12, 0.08],
        [-0.85,-0.6, -0.25, 0.0],
        [-0.78,-0.58, -0.42, -0.12],
        [-1.25,-1.0, -0.52, -0.35],
    ];

    function isBrazil(lon, lat) {
        for (let i = 0; i < brazil.length; i++) {
            const b = brazil[i];
            if (lon >= b[0] && lon <= b[1] && lat >= b[2] && lat <= b[3]) return true;
        }
        return false;
    }

    function isLand(lon, lat) {
        if (isBrazil(lon, lat)) return 2; // 2 = Brasil
        for (let i = 0; i < landMasses.length; i++) {
            const c = landMasses[i];
            if (lon >= c[0] && lon <= c[1] && lat >= c[2] && lat <= c[3]) return 1; // 1 = terra
        }
        return 0; // 0 = oceano
    }

    let globeAngle = 0;
    const globeCx = Math.floor(cols * 0.25);
    const globeCy = Math.floor(rows * 0.48);
    const globeR = Math.min(cols * 0.18, rows * 0.38);

    function draw() {
        globeAngle += 0.003;

        ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.font = fontSize + 'px monospace';

        // 1. Cascata de código multidirecional
        streams.forEach(s => {
            s.update();
            s.chars.forEach((cObj, i) => {
                let px = cObj.x * fontSize;
                let py = cObj.y * fontSize;
                const mouseDist = Math.hypot(px - mouseX, py - mouseY);
                if (mouseDist < 80) {
                    ctx.fillStyle = '#ffffff';
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

        // 2. Globo terrestre 3D
        const x1 = Math.max(0, globeCx - globeR - 2);
        const x2 = Math.min(Math.floor(cols * 0.5), globeCx + globeR + 2);
        const y1 = Math.max(0, globeCy - globeR - 2);
        const y2 = Math.min(rows, globeCy + globeR + 2);

        for (let gx = x1; gx < x2; gx++) {
            for (let gy = y1; gy < y2; gy++) {
                const dx = gx - globeCx;
                const dy = gy - globeCy;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist > globeR) continue;

                const nx = dx / globeR;
                const ny = dy / globeR;
                const nz = Math.sqrt(Math.max(0, 1 - nx * nx - ny * ny));
                if (nz < 0.01) continue;

                // Rotação Y
                const rx = nx * Math.cos(globeAngle) + nz * Math.sin(globeAngle);
                const rz = -nx * Math.sin(globeAngle) + nz * Math.cos(globeAngle);
                if (rz < 0) continue;

                const lon = Math.atan2(rx, rz);
                const lat = Math.asin(Math.max(-1, Math.min(1, ny)));
                const land = isLand(lon, -lat);

                // Atmosfera na borda
                const edgeDist = 1 - dist / globeR;

                // Densidade e cor
                let intensity, r, g, b;
                const lighting = 0.3 + rz * 0.5;

                if (land === 2) {
                    // ══ BRASIL — verde, azul e amarelo ══
                    const brNoise = Math.sin(lon * 40 + lat * 40);
                    if (brNoise > 0.3) {
                        // Verde
                        r = 0; g = 180 + Math.floor(lighting * 75); b = 30;
                    } else if (brNoise > -0.3) {
                        // Amarelo
                        r = 220 + Math.floor(lighting * 35); g = 200 + Math.floor(lighting * 55); b = 0;
                    } else {
                        // Azul
                        r = 0; g = 80 + Math.floor(lighting * 40); b = 180 + Math.floor(lighting * 75);
                    }
                    intensity = 0.6 + lighting * 0.35;
                } else if (land === 1) {
                    // ══ Outros países — verde Matrix ══
                    r = 0;
                    g = 100 + Math.floor(lighting * 100);
                    b = 30 + Math.floor(lighting * 20);
                    intensity = 0.25 + lighting * 0.35;
                } else {
                    // ══ Oceano — escuro com grid ══
                    const gridLon = Math.abs(lon % 0.5) < 0.025;
                    const gridLat = Math.abs(lat % 0.5) < 0.025;
                    if (gridLon || gridLat) {
                        r = 0; g = 60; b = 30; intensity = 0.15;
                    } else {
                        r = 0; g = 25; b = 15; intensity = 0.04;
                    }
                }

                // Atmosfera glow na borda
                if (edgeDist < 0.1) {
                    intensity = Math.max(intensity, 0.35 * (1 - edgeDist / 0.1));
                    g = Math.max(g, 150);
                }

                // Filtra por densidade
                if (Math.random() > intensity * 0.85 + 0.15) continue;

                const px = gx * fontSize;
                const py = gy * fontSize;
                const char = chars[Math.floor(Math.random() * chars.length)];

                // Mouse interaction
                const mDist = Math.hypot(px - mouseX, py - mouseY);
                if (mDist < 120) {
                    const prox = 1 - mDist / 120;
                    ctx.fillStyle = `rgba(200, 255, 220, ${0.4 + prox * 0.6})`;
                    ctx.shadowBlur = 6 + prox * 10;
                    ctx.shadowColor = land === 2 ? '#ffdd00' : '#00ff41';
                } else {
                    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.4 + intensity * 0.55})`;
                    if (land === 2) {
                        ctx.shadowBlur = 3;
                        ctx.shadowColor = `rgba(${r}, ${g}, ${b}, 0.5)`;
                    } else if (intensity > 0.45) {
                        ctx.shadowBlur = 3;
                        ctx.shadowColor = '#00ff41';
                    } else {
                        ctx.shadowBlur = 0;
                    }
                }
                ctx.fillText(char, px, py);
                ctx.shadowBlur = 0;
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