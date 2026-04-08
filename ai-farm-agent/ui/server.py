"""
UI Server v11 — Upgrade do v9.
MUDANCAS:
- Passa params do Maestro para Desktop Agent
- NAO tira screenshot durante acoes desktop (evita roubar foco)
- NAO restaura browser entre passos (so no final)
- Retry para acoes visuais que falham
- Salva workflow bem-sucedido na memoria
- Action Logger registra cada acao
"""
import os, threading, time, traceback
from flask import Flask, render_template, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from agents.maestro import Maestro
from agents.data_agent import DataAgent
from agents.web_agent import WebAgent
from agents.code_agent import CodeAgent
from agents.desktop_agent import DesktopAgent
from agents.file_agent import FileAgent
from core.automation import AutomationEngine
from core.capture import ScreenCapture
from core.narrator import ReportNarrator

# Opcionais — nao travam se falharem
try:
    from agents.vision_maestro import VisionMaestro
except:
    VisionMaestro = None

app = Flask(__name__,
    template_folder=os.path.join(os.path.dirname(__file__),"templates"),
    static_folder=os.path.join(os.path.dirname(__file__),"static"))
app.config["SECRET_KEY"] = "ai-farm-v11"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

maestro = Maestro()
agents = {"DATA":DataAgent(),"WEB":WebAgent(),"CODE":CodeAgent(),"DESKTOP":DesktopAgent(),"FILE":FileAgent()}
engine = AutomationEngine()
capture = ScreenCapture()
narrator = ReportNarrator()
state = {"running":False}
api_usage = {"calls":0,"tokens_est":0}

# Acoes que NÃO devem tirar screenshot (para nao roubar foco)
NO_SCREENSHOT = {"wait","hotkey","type_text","app_type","app_search","focus_window",
    "vision_click","vision_type","uia_click","uia_type","run_python","run_command",
    "write_file","create_folder","read_file","list_files","move_file","copy_file",
    "delete_file","find_files","pip_install","excel_write","wait_for_window","wait_for_element"}

# Acoes visuais que merecem retry se falharem
RETRY_ACTIONS = {"vision_click","vision_type","uia_click","uia_type"}

@app.route("/")
def index(): return render_template("index.html")
@app.route("/captures/<path:f>")
def serve_cap(f): return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)),"captures"),f)
@app.route("/reports/<path:f>")
def serve_rep(f): return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__)),"reports"),f)
@socketio.on("connect")
def on_connect(): emit("status",{"type":"connected","msg":"Pronto"})
@socketio.on("execute_task")
def on_execute(data):
    task=data.get("task","").strip()
    if not task or state["running"]: emit("error",{"msg":"Vazio ou em execucao"}); return
    threading.Thread(target=_run,args=(task,data.get("dry_run",False),data.get("generate_report",True)),daemon=True).start()
@socketio.on("force_stop")
def on_stop():
    state["running"]=False
    emit("cancelled",{"msg":"Parado"})

def _run(task,dry_run,gen_report):
    state["running"]=True
    all_success = True
    try:
        socketio.emit("phase",{"phase":"maestro","msg":"Analisando..."})
        api_usage["calls"]+=1; api_usage["tokens_est"]+=500
        plan=maestro.analyze(task)
        if plan.get("error"): socketio.emit("error",{"msg":plan.get("message","Erro")}); return
        subtasks=plan.get("subtasks",[])
        socketio.emit("plan_ready",{"plan":{"task_summary":plan.get("analysis",""),
            "steps":[{"step":i+1,"description":"["+s["agent"]+"] "+s["task"],"action":s["agent"]} for i,s in enumerate(subtasks)],
            "skills":plan.get("skills",[])}})

        capture.clear_records(); all_records=[]; context={}; step_n=0

        for si,subtask in enumerate(subtasks):
            if not state["running"]: socketio.emit("cancelled",{"msg":"Cancelado"}); return
            agent_name=subtask.get("agent","").upper()
            agent=agents.get(agent_name)
            if not agent: continue

            socketio.emit("phase",{"phase":"agent","msg":agent_name+" Agent..."})

            # UPGRADE: Passa params estruturados para Desktop Agent
            subtask_params = subtask.get("params", {})
            agent_task = subtask.get("task", "")

            if agent_name == "DESKTOP" and subtask_params and subtask_params.get("app"):
                # Desktop recebe params do Maestro → usa atalhos de teclado
                agent_plan = agent.plan({"task": agent_task, "params": subtask_params}, context=subtask_params)
            else:
                api_usage["calls"]+=1; api_usage["tokens_est"]+=1000
                dep=subtask.get("depends_on")
                agent_plan=agent.plan(agent_task, context=context.get("sub_"+str(dep)) if dep else None)

            if agent_plan.get("error"): continue

            agent_steps=agent_plan.get("steps",[])
            sub_results=[]
            is_desktop = agent_name == "DESKTOP"

            for j,step in enumerate(agent_steps):
                if not state["running"]: socketio.emit("cancelled",{"msg":"Cancelado"}); return
                step_n+=1
                action=step.get("action",""); params=step.get("params",{}); desc=step.get("description","")
                start_time = time.time()

                socketio.emit("step_start",{"step":step_n,"total":step_n+len(agent_steps)-j-1,
                    "desc":"["+agent_name+"] "+desc,"action":action,"progress":round(si/len(subtasks)*100)})

                # EXECUTA
                result=engine.execute(action,params,dry_run=dry_run)

                # UPGRADE: Retry para acoes visuais que falharam
                if not result.get("success",True) and action in RETRY_ACTIONS and not dry_run:
                    time.sleep(2)
                    result=engine.execute(action,params,dry_run=dry_run)

                if not result.get("success", True):
                    all_success = False

                # UPGRADE: Log da acao
                duration = int((time.time() - start_time) * 1000)
                try:
                    from core.action_logger import log_action
                    log_action(agent_name, action, params, result, duration_ms=duration)
                except: pass

                all_records.append(result); sub_results.append(result.get("result",""))

                # UPGRADE: Screenshot SOMENTE para acoes de codigo, NAO desktop
                cap=None
                if not dry_run and action not in NO_SCREENSHOT and not is_desktop:
                    try: cap=capture.capture_step(step_n,desc,action,result.get("result",""))
                    except: pass

                # UPGRADE: NUNCA restaura browser entre passos
                # O browser fica minimizado ate o final de TODA a tarefa

                socketio.emit("step_done",{"step":step_n,"total":step_n+len(agent_steps)-j-1,
                    "ok":result.get("success",False),"result":result.get("result",""),
                    "desc":"["+agent_name+"] "+desc,"action":action,
                    "screenshot":cap.get("filename") if cap and cap.get("filename") else None,
                    "progress":round((si+1)/len(subtasks)*100)})
                socketio.emit("api_usage",api_usage)
                time.sleep(0.05)

            context["sub_"+str(si+1)]={"agent":agent_name,"results":sub_results}

        # Restaura browser SOMENTE no final de tudo
        if engine.vision:
            try: engine.vision.restore_browser()
            except: pass

        # UPGRADE: Salva workflow se deu certo
        if all_success and not dry_run:
            try:
                from memory.workflow_store import save_workflow
                save_workflow(task, [r.get("result","") for r in all_records], subtasks[0].get("agent",""), True)
            except: pass

        socketio.emit("task_done",{"msg":"Concluido","steps":step_n,"dry_run":dry_run,"skills":plan.get("skills",[])})
        if gen_report and not dry_run:
            socketio.emit("phase",{"phase":"reporting","msg":"Relatorio..."})
            api_usage["calls"]+=1; api_usage["tokens_est"]+=1500
            report=narrator.generate_report(task,all_records,capture.get_captures_as_base64(3))
            socketio.emit("report_ready",{"report":report})
    except Exception as e:
        socketio.emit("error",{"msg":str(e)}); traceback.print_exc()
    finally:
        state["running"]=False
        if engine.vision:
            try: engine.vision.restore_browser()
            except: pass