/* ══════════════════════════════════════ */
/* AI Farm Agent v2.0 — Frontend        */
/* ══════════════════════════════════════ */

const S = { c: false, r: false, s: { dryRun: false, genReport: true }, tasks: 0, xp: 0 };
let sk;

// Dados atualizados com Glifos Sofisticados e Tradução para o Português
const hologramData = {
    'autonomous': {
        glyph: '❖',
        title: 'MODO AUTÔNOMO',
        desc: 'DIRETRIZ CENTRAL // MODO AUTÔNOMO ATIVO'
    },
    'computer': {
        glyph: '🖳',
        title: 'LINK DO SISTEMA',
        desc: 'INTERFACE DE HARDWARE // CONEXÃO DE SISTEMA ESTÁVEL'
    },
    'operator': {
        glyph: '웃',
        title: 'PROXY HUMANO',
        desc: 'SOBRECARGA MANUAL // CONTROLE HUMANO INICIADO'
    }
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

    // ═══ GLOBO 3D — Continentes + Siglas + Empresas de IA por hover ═══
    const countries = [
        [-1.28,-0.6,-0.55,0.08,"BR","SA"],[-1.22,-1.02,-0.85,-0.28,"AR","SA"],
        [-1.42,-1.22,-0.25,0.0,"PE","SA"],[-1.32,-1.1,0.0,0.2,"CO","SA"],
        [-1.4,-1.2,0.02,0.15,"VE","SA"],[-1.28,-1.18,-0.95,-0.25,"CL","SA"],
        [-1.2,-1.05,-0.3,-0.12,"BO","SA"],[-1.05,-0.92,-0.42,-0.28,"PY","SA"],
        [-0.98,-0.88,-0.58,-0.48,"UY","SA"],
        [-2.15,-1.25,0.52,0.85,"USA","NA"],[-2.5,-1.1,0.82,1.22,"CA","NA"],
        [-1.95,-1.55,0.32,0.55,"MX","NA"],[-2.95,-2.55,1.0,1.18,"AK","NA"],
        [-1.48,-1.3,0.35,0.4,"CU","NA"],
        [-0.18,0.05,0.58,0.75,"ES","EU"],[-0.08,0.12,0.68,0.85,"FR","EU"],
        [-0.1,0.05,0.85,0.98,"UK","EU"],[0.08,0.28,0.82,0.98,"DE","EU"],
        [0.12,0.28,0.6,0.78,"IT","EU"],[0.35,0.55,0.78,0.95,"PL","EU"],
        [0.08,0.25,0.98,1.18,"NO","EU"],[0.15,0.32,1.0,1.15,"SE","EU"],
        [0.42,0.65,0.62,0.72,"TR","EU"],
        [-0.05,0.55,0.35,0.55,"DZ","AF"],[0.35,0.62,0.35,0.55,"EG","AF"],
        [-0.2,0.18,0.2,0.38,"NG","AF"],[0.25,0.55,-0.58,-0.2,"ZA","AF"],
        [0.62,0.82,0.02,0.18,"ET","AF"],[0.35,0.65,-0.08,0.15,"CD","AF"],
        [0.15,0.55,0.0,0.25,"SD","AF"],
        [0.5,2.8,0.88,1.2,"RU","AS"],[1.3,2.15,0.5,0.82,"CN","AS"],
        [1.1,1.42,0.08,0.5,"IN","AS"],[2.25,2.48,0.5,0.75,"JP","AS"],
        [2.15,2.28,0.55,0.68,"KR","AS"],[1.55,1.85,0.25,0.42,"TH","AS"],
        [0.82,0.98,0.42,0.58,"IR","AS"],[0.62,0.88,0.25,0.42,"SAU","AS"],
        [1.0,1.3,0.5,0.7,"PK","AS"],[1.65,1.92,0.05,0.28,"ID","AS"],
        [0.72,0.85,0.42,0.55,"IQ","AS"],
        [1.95,2.65,-0.62,-0.18,"AU","OC"],[2.85,3.0,-0.72,-0.52,"NZ","OC"],
        [-0.9,-0.45,1.05,1.3,"GL","NA"]
    ];

    const landFill = [
        [-1.05,-0.92,-0.42,-0.28,"","SA"],[-1.25,-1.0,-0.52,-0.35,"","SA"],
        [-0.85,-0.6,-0.25,0.0,"","SA"],[-1.15,-0.72,-0.12,0.08,"","SA"],
        [-1.55,-1.28,0.42,0.58,"","NA"],[-2.3,-1.8,1.05,1.2,"","NA"],
        [-1.58,-1.38,0.15,0.32,"","NA"],[-1.48,-1.35,0.1,0.22,"","NA"],
        [-0.15,0.25,0.55,0.68,"","EU"],[0.25,0.45,0.6,0.75,"","EU"],
        [0.55,0.75,0.78,1.0,"","EU"],[0.7,2.5,0.92,1.12,"","AS"],
        [1.0,3.0,0.85,1.08,"","AS"],[0.5,1.0,0.5,0.7,"","AS"],
        [1.2,1.8,0.05,0.4,"","AS"],[1.35,1.42,0.05,0.12,"","AS"],
        [1.8,2.35,-0.15,0.05,"","AS"],[1.5,1.72,0.75,0.85,"","AS"],
        [0.0,0.5,-0.5,0.0,"","AF"],[-0.25,0.1,0.12,0.3,"","AF"],
        [0.1,0.48,-0.05,0.1,"","AF"],[-0.3,-0.05,0.08,0.2,"","AF"],
        [0.5,0.72,-0.2,0.08,"","AF"],[0.72,0.82,-0.4,-0.2,"","AF"],
        [-0.2,0.15,0.38,0.55,"","AF"],[2.0,2.55,-0.55,-0.22,"","OC"],
        [2.4,2.6,-0.12,0.0,"","OC"]
    ];

    const CC = {
        SA:[0,220,60], NA:[50,140,255], EU:[220,180,40],
        AF:[230,120,30], AS:[220,50,80], OC:[0,210,210],
    };

    const aiCompanies = {
        SA: {name:"SOUTH AMERICA",companies:["Nubank AI","iFood ML","TOTVS Carol","Semantix","Tempest AI","Movile Labs"]},
        NA: {name:"NORTH AMERICA",companies:["OpenAI","Anthropic","Google DeepMind","Meta AI","NVIDIA","xAI","Microsoft","Amazon AWS AI","Apple ML","Tesla AI"]},
        EU: {name:"EUROPE",companies:["Mistral AI","DeepL","Aleph Alpha","Stability AI","BioNTech AI","Graphcore","Darktrace","Exscientia"]},
        AF: {name:"AFRICA",companies:["InstaDeep","Lelapa AI","Zindi","Masakhane NLP","Ushahidi AI","54gene ML"]},
        AS: {name:"ASIA",companies:["Baidu AI","Alibaba DAMO","Tencent AI","ByteDance","Samsung AI","SoftBank","Yandex","Huawei AI","SenseTime","Infosys AI"]},
        OC: {name:"OCEANIA",companies:["Canva AI","Atlassian Intelligence","Appen","SafetyCulture AI","Harrison.ai","Nearmap AI"]},
    };

    function identifyPoint(lon, lat) {
        for (let i = 0; i < countries.length; i++) {
            const c = countries[i];
            if (lon >= c[0] && lon <= c[1] && lat >= c[2] && lat <= c[3]) return {cont:c[5],tag:c[4]};
        }
        for (let i = 0; i < landFill.length; i++) {
            const c = landFill[i];
            if (lon >= c[0] && lon <= c[1] && lat >= c[2] && lat <= c[3]) return {cont:c[5],tag:""};
        }
        return null;
    }

    let globeAngle = 0;
    const globeCx = Math.floor(cols * 0.25);
    const globeCy = Math.floor(rows * 0.48);
    const globeR = Math.min(cols * 0.18, rows * 0.38);
    let hoveredContinent = null;

    const cCenters = countries.filter(c=>c[4]).map(c=>({
        lon:(c[0]+c[1])/2, lat:-(c[2]+c[3])/2, tag:c[4], cont:c[5]
    }));

    function project(lon, lat) {
        const sy = -Math.sin(lat);
        const cy2 = Math.cos(lat);
        const sx = cy2 * Math.sin(lon);
        const sz = cy2 * Math.cos(lon);
        const prx = sx * Math.cos(globeAngle) + sz * Math.sin(globeAngle);
        const prz = -sx * Math.sin(globeAngle) + sz * Math.cos(globeAngle);
        if (prz < 0.05) return null;
        return {
            x: (globeCx + prx * globeR) * fontSize,
            y: (globeCy + sy * globeR) * fontSize,
            z: prz
        };
    }

    function detectContinent(mx, my) {
        const gx = mx / fontSize;
        const gy = my / fontSize;
        const dx = gx - globeCx;
        const dy = gy - globeCy;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist > globeR) return null;

        const nx = dx / globeR;
        const ny = dy / globeR;
        const nz = Math.sqrt(Math.max(0, 1-nx*nx-ny*ny));
        if (nz < 0.01) return null;

        const rx = nx*Math.cos(globeAngle) + nz*Math.sin(globeAngle);
        const rz = -nx*Math.sin(globeAngle) + nz*Math.cos(globeAngle);
        if (rz < 0) return null;

        const lon = Math.atan2(rx, rz);
        const lat = -Math.asin(Math.max(-1, Math.min(1, ny)));
        const info = identifyPoint(lon, lat);
        return info ? info.cont : null;
    }

    function draw() {
        globeAngle += 0.003;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.12)';
        ctx.fillRect(0, 0, c.width, c.height);
        ctx.font = fontSize + 'px monospace';

        hoveredContinent = detectContinent(mouseX, mouseY);

        // 1. Cascata de código
        streams.forEach(s => {
            s.update();
            s.chars.forEach((cObj, i) => {
                let px = cObj.x * fontSize;
                let py = cObj.y * fontSize;
                const md = Math.hypot(px - mouseX, py - mouseY);
                if (md < 80) {
                    ctx.fillStyle = '#ffffff';
                    const a = Math.atan2(py - mouseY, px - mouseX);
                    px += Math.cos(a) * 10; py += Math.sin(a) * 10;
                    ctx.fillText(chars[Math.floor(Math.random() * chars.length)], px, py);
                } else {
                    const al = 1 - (i / s.length);
                    ctx.fillStyle = (i === 0) ? '#ffffff' : `rgba(0,255,65,${al})`;
                    ctx.fillText(cObj.char, px, py);
                }
            });
        });

        // 2. Globo terrestre
        const x1 = Math.max(0, globeCx - globeR - 2);
        const x2 = Math.min(Math.floor(cols * 0.52), globeCx + globeR + 2);
        const y1 = Math.max(0, globeCy - globeR - 2);
        const y2 = Math.min(rows, globeCy + globeR + 2);

        for (let gx = x1; gx < x2; gx++) {
            for (let gy = y1; gy < y2; gy++) {
                const dx = gx - globeCx, dy = gy - globeCy;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist > globeR) continue;

                const nx = dx/globeR, ny = dy/globeR;
                const nz = Math.sqrt(Math.max(0, 1-nx*nx-ny*ny));
                if (nz < 0.01) continue;

                const rx = nx*Math.cos(globeAngle) + nz*Math.sin(globeAngle);
                const rz = -nx*Math.sin(globeAngle) + nz*Math.cos(globeAngle);
                if (rz < 0) continue;

                const lon = Math.atan2(rx, rz);
                const lat = Math.asin(Math.max(-1, Math.min(1, ny)));
                const info = identifyPoint(lon, -lat);
                const edgeDist = 1 - dist / globeR;
                const light = 0.25 + rz * 0.55;

                let r, g, b, intensity;
                const isHovered = info && hoveredContinent === info.cont;

                if (info) {
                    const cc = CC[info.cont] || [0,200,60];
                    const boost = isHovered ? 1.4 : 1;
                    r = Math.min(255, Math.floor(cc[0] * light * boost));
                    g = Math.min(255, Math.floor(cc[1] * light * boost));
                    b = Math.min(255, Math.floor(cc[2] * light * boost));
                    intensity = isHovered ? 0.5 + light * 0.45 : 0.3 + light * 0.4;
                } else {
                    const gl = Math.abs(lon % 0.5) < 0.02 || Math.abs(lat % 0.5) < 0.02;
                    r = 0; g = gl ? 40 : 15; b = gl ? 25 : 10;
                    intensity = gl ? 0.1 : 0.03;
                }

                if (edgeDist < 0.09) {
                    const gw = 0.35 * (1 - edgeDist / 0.09);
                    intensity = Math.max(intensity, gw); g = Math.max(g, 120);
                }
                if (Math.random() > intensity * 0.82 + 0.18) continue;

                const px = gx * fontSize, py = gy * fontSize;
                const ch = chars[Math.floor(Math.random() * chars.length)];

                ctx.fillStyle = `rgba(${r},${g},${b},${0.4 + intensity * 0.55})`;
                ctx.shadowBlur = (isHovered && intensity > 0.4) ? 5 : (intensity > 0.5 ? 2 : 0);
                ctx.shadowColor = isHovered ? '#ffffff' : `rgba(${r},${g},${b},0.4)`;
                ctx.fillText(ch, px, py);
                ctx.shadowBlur = 0;
            }
        }

        // 3. Siglas dos países sobre o globo (CORRIGIDO: Fixadas)
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle'; 
        for (let i = 0; i < cCenters.length; i++) {
            const cc = cCenters[i];
            const p = project(cc.lon, cc.lat);
            
            if (!p || p.z < 0.4) continue;

            const isH = hoveredContinent === cc.cont;
            const col = CC[cc.cont] || [0,200,60];
            const alpha = (0.4 + p.z * 0.6) * (isH ? 1 : 0.7);

            ctx.font = isH ? 'bold 11px monospace' : '9px monospace';
            ctx.fillStyle = `rgba(${Math.min(255,col[0]+90)},${Math.min(255,col[1]+90)},${Math.min(255,col[2]+90)},${alpha})`;
            ctx.shadowBlur = isH ? 6 : 2;
            ctx.shadowColor = `rgba(${col[0]},${col[1]},${col[2]},0.5)`;
            ctx.fillText(cc.tag, p.x, p.y);
            ctx.shadowBlur = 0;
        }
        ctx.textAlign = 'start';
        ctx.textBaseline = 'alphabetic'; 
        ctx.font = fontSize + 'px monospace';

        // 4. HUD de empresas de IA (CORRIGIDO: Proteção de Bordas)
        if (hoveredContinent && aiCompanies[hoveredContinent]) {
            const data = aiCompanies[hoveredContinent];
            const col = CC[hoveredContinent];
            
            const hudW = 220;
            const hudH = 24 + data.companies.length * 18;

            let hudX = mouseX + 15;
            let hudY = mouseY - (hudH / 2);

            // Proteção para não vazar a tela na direita
            if (hudX + hudW > window.innerWidth - 20) {
                hudX = mouseX - hudW - 15;
            }
            // Proteção vertical (topo e base)
            if (hudY < 20) hudY = 20;
            if (hudY + hudH > window.innerHeight - 20) hudY = window.innerHeight - hudH - 20;

            // Fundo do HUD
            ctx.fillStyle = 'rgba(0,0,0,0.85)';
            ctx.strokeStyle = `rgba(${col[0]},${col[1]},${col[2]},0.8)`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.roundRect(hudX, hudY, hudW, hudH, 4);
            ctx.fill();
            ctx.stroke();

            // Título do continente
            ctx.font = 'bold 11px monospace';
            ctx.fillStyle = `rgb(${Math.min(255,col[0]+60)},${Math.min(255,col[1]+60)},${Math.min(255,col[2]+60)})`;
            ctx.shadowBlur = 6;
            ctx.shadowColor = `rgba(${col[0]},${col[1]},${col[2]},0.6)`;
            ctx.textAlign = 'left';
            ctx.fillText('⬡ ' + data.name + ' — AI', hudX + 10, hudY + 16);
            ctx.shadowBlur = 0;

            // Lista de empresas
            ctx.font = '10px monospace';
            data.companies.forEach((company, idx) => {
                const yPos = hudY + 34 + idx * 18;
                const flicker = Math.sin(Date.now() * 0.003 + idx) * 0.15;
                ctx.fillStyle = `rgba(${col[0]},${col[1]},${col[2]},${0.8 + flicker})`;
                ctx.fillText('› ' + company, hudX + 12, yPos);
            });

            ctx.font = fontSize + 'px monospace';
        }

        requestAnimationFrame(draw);
    }
    draw();

    window.addEventListener('resize', () => {
        c.width = window.innerWidth;
        c.height = window.innerHeight;
    });
}

/* ═══ HOVER HUD DATA PROFILE DAS PALAVRAS (ATUALIZADO COM GLIFOS E HTML) ═══ */
function initHoverReveal() {
    const hoverElements = document.querySelectorAll('.matrix-hover');
    const revealContainer = document.getElementById('hover-reveal-container');

    if (!revealContainer || hoverElements.length === 0) return;

    hoverElements.forEach(el => {
        el.addEventListener('mouseenter', (e) => {
            const dataKey = el.textContent.trim().toLowerCase();
            const data = hologramData[dataKey];
            
            if (!data) return;

            // Renderiza o HTML interno com estilo inline (compatível com seu CSS base)
            revealContainer.innerHTML = `
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px; border-bottom: 1px solid rgba(0, 255, 65, 0.3); padding-bottom: 8px;">
                    <span style="font-size: 28px; color: #00ff41; text-shadow: 0 0 10px #00ff41;">${data.glyph}</span>
                    <h4 style="margin: 0; font-size: 14px; font-family: monospace; color: #fff; text-shadow: 0 0 8px #00ff41; letter-spacing: 1px;">${data.title}</h4>
                </div>
                <p style="margin: 0; font-size: 11px; font-family: monospace; color: #00e5ff; opacity: 0.9;">${data.desc}</p>
            `;
            
            revealContainer.style.opacity = '1';
            revealContainer.classList.add('glitch-anim');
            setTimeout(() => revealContainer.classList.remove('glitch-anim'), 300);
        });

        el.addEventListener('mousemove', (e) => {
            const x = e.clientX + 20;
            const y = e.clientY + 20;
            revealContainer.style.transform = `translate(${x}px, ${y}px) scale(1) skew(0deg)`;
        });

        el.addEventListener('mouseleave', (e) => {
            revealContainer.style.opacity = '0';
            const x = e.clientX + 20;
            const y = e.clientY + 20;
            revealContainer.style.transform = `translate(${x}px, ${y}px) scale(0.8) skew(10deg)`;
        });
    });
}

/* ═══ OUTRAS FUNÇÕES DA APLICAÇÃO GERAL ═══ */
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
    initMatrixEngine(); 
    initHoverReveal();  
    initSocket();
    
    $('task-input').addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); go(); }
    });
    lg('info', 'AI FARM AGENT v2.0 — READY');
});