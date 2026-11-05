"""
Verifica o segundo cerebro contra o historico local, preservando as notas de origem.

- Conta sucessos/falhas de cada tarefa de referencia (execucoes parecidas, mesmo agente).
- --apply: atualiza evidencia das notas com execucoes correspondentes, sem remover fontes.
- --restore: copia referencias do arquivo antigo de volta ao vault, sem substituir notas.

Uso:
    python scripts/brain_verify.py            # relatorio, nao mexe em nada
    python scripts/brain_verify.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true", help="restaurar copias ausentes do arquivo antigo")
    args = ap.parse_args()
    from core.brain import get_brain
    from core.memory_gate import verify_all, routing_map, restore_references
    vault = get_brain().root
    if args.restore:
        print(f"Referencias copiadas (originais preservados): {len(restore_references(vault))}")
    rep = verify_all(vault, apply=args.apply)
    print(f"verificadas: {len(rep['verificadas'])} | restauradas: {len(rep['restauradas'])} | "
          f"rebaixadas: {len(rep['rebaixadas'])} | hipoteses: {len(rep['hipoteses'])}")
    for k in ("verificadas", "restauradas", "rebaixadas"):
        for n in rep[k]:
            print(f"  [{k[:-1]}] {n['sucessos']}✓ {n['falhas']}✗ {n['ultima'] or '-'} {n['nota']}")
    if args.apply:
        (vault / "00 Maestro" / "Mapa de roteamento.md").write_text(routing_map(vault), encoding="utf-8")
        print("\nMapa de roteamento atualizado.")


if __name__ == "__main__":
    main()
