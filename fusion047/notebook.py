"""Build the two-cell Colab notebook with immutable artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = 'f4b9abd30b3adf72a0f7bae46282e83cd19f6d37'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(text):
    return dedent(text).strip().splitlines(keepends=True)


def make(commit, output):
    runtime = ROOT/'fusion047'/'torch_runtime.py'
    head = ROOT/'fusion047'/'checkpoints'/'identity-head.npz'
    notebook = {
        'cells': [
            {'cell_type':'markdown','metadata':{},'source':lines("""
                # Liquid Sense × Gemma 047

                No Colab, escolha **Ambiente de execução → Alterar tipo de ambiente de execução → T4 GPU**. Execute a célula 1 para baixar os pesos verificados e carregar o modelo na GPU. Desmarque **usar_t4** para testar em CPU. O download de 2,65 GB fica na máquina da sessão.

                Execute a célula 2 para enviar sua pergunta. Cada execução da célula 2 é uma nova conversa e reaproveita o modelo que já está em memória.
            """)},
        ],
        'metadata': {'colab':{'name':'Liquid Sense × Gemma 047'},
                     'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},
        'nbformat':4,'nbformat_minor':0,
    }
    setup = r'''
        #@title 1. Preparar o Liquid Sense 047
        usar_t4 = True #@param {type:"boolean"}

        import hashlib
        import importlib.util
        import os
        from pathlib import Path
        import subprocess
        import sys
        from urllib.request import urlopen
        import torch

        if usar_t4 and not torch.cuda.is_available():
            raise RuntimeError("Selecione T4 GPU no Colab ou desmarque usar_t4 para executar em CPU.")
        if usar_t4:
            probe = torch.ones((8, 8), dtype=torch.float16, device="cuda")
            try:
                verified = torch.mm(probe, probe, out_dtype=torch.float32)
            except TypeError as error:
                raise RuntimeError("Use PyTorch 2.8 ou posterior para o modo T4.") from error
            if verified[0, 0].item() != 8:
                raise RuntimeError("O teste de multiplicação FP16 da GPU falhou.")
            del probe, verified
        if importlib.util.find_spec("tokenizers") is None:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "tokenizers>=0.22,<0.24"], check=True)

        device = "cuda" if usar_t4 else "cpu"
        torch.set_num_threads(2)
        repo = "https://raw.githubusercontent.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-"
        work = Path(os.environ.get("LIQUID_047_NOTEBOOK_DIR", "/content/liquid-sense-046")).resolve()
        work.mkdir(parents=True, exist_ok=True)

        def sha(path):
            with path.open("rb") as file:
                return hashlib.file_digest(file, "sha256").hexdigest()

        def download(url, path, expected, maximum):
            if path.is_file() and sha(path) == expected:
                return
            with urlopen(url, timeout=45) as response:
                data = response.read(maximum + 1)
            if len(data) > maximum or hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError(f"SHA-256 inválido em {path.name}.")
            path.write_bytes(data)

        old_commit = "OLD_COMMIT"
        package_commit = "PACKAGE_COMMIT"
        parent = work / "LiquidSense-Gemma-045.lsmix"
        expected_parent = "e6e4528057543f0bdf35305c87b79197c639f2d77ddfcf140745a62f4441703c"
        if not parent.is_file() or sha(parent) != expected_parent:
            recovery = work / "recuperar.py"
            download(f"{repo}/{old_commit}/fusion046/recover.py", recovery,
                     "e5cd87bc643cf94905888e6a61f9838fc5b8591832a801a06682b58ed38452a6", 16000)
            print("Baixando os pesos para a sessão da nuvem…", flush=True)
            subprocess.run([sys.executable, str(recovery), str(parent)], check=True)

        readout = work / "readout.lscal"
        readout_sha = "941daca310736af121cdd337317b5e1bddb741b88ea085d684d3760ecc1fecfd"
        download(f"{repo}/{old_commit}/fusion046/checkpoints/readout.lscal", readout, readout_sha, 250000)
        identity = work / "identity-head.npz"
        identity_sha = "IDENTITY_SHA"
        download(f"{repo}/{package_commit}/fusion047/checkpoints/identity-head.npz", identity, identity_sha, 500000)
        backend = work / "torch_runtime.py"
        download(f"{repo}/{package_commit}/fusion047/torch_runtime.py", backend, "BACKEND_SHA", 40000)
        spec = importlib.util.spec_from_file_location("liquid_sense_torch", backend)
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        nome = torch.cuda.get_device_name(0) if usar_t4 else "CPU"
        print(f"Carregando Liquid Sense 047 em {nome}…", flush=True)
        model = runtime.LiquidSenseTorch(parent, readout, readout_sha, device, verified_parent=True,
                                         identity=identity, identity_sha=identity_sha)
        print(f"Liquid Sense 047 pronto em {nome}.")
    '''
    setup = (setup.replace('OLD_COMMIT',PREVIOUS).replace('PACKAGE_COMMIT',commit)
             .replace('IDENTITY_SHA',sha(head)).replace('BACKEND_SHA',sha(runtime)))
    chat = '''
        #@title 2. Perguntar ao Liquid Sense 047
        pergunta = "Como devo chamar o modelo com que estou conversando? Só o nome." #@param {type:"string"}
        modo_pensar = False #@param {type:"boolean"}
        limite_resposta = 128 #@param {type:"integer"}

        print("Gerando resposta…", flush=True)
        resultado = model.generate(pergunta, thinking=modo_pensar, response_tokens=limite_resposta)
        print("\\nLiquid Sense 047\\n" + resultado["text"])
        print(f"\\n{nome} · {resultado['tokens']} tokens · {resultado['seconds']:.2f} s")
    '''
    for source in (setup, chat):
        source = lines(source)
        compile(''.join(source), output.name, 'exec')
        notebook['cells'].append(dict(cell_type='code',metadata={},source=source,
                                      execution_count=None,outputs=[]))
    output.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit')
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    make(args.commit,args.output)
