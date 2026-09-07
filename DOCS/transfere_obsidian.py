import shutil
import os
from pathlib import Path
import time


PASTA_DOCS_VS_CODE = Path(r"DOCS")


PASTA_OBSIDAN = Path(r"G:\Meu Drive\Obsidian")
PASTA_PROJETO_SENSOR_VIBRAÇÃO_OBSIDAN = Path(r"G:\Meu Drive\Obsidian\5.PROJETOS\5.2 Projeto sensor vibração")
readme = Path("README.md")

arquivos_ignorar = [
    "transfere_obsidian.py",
    "superpowers",
    
]

def copia_docs_para_obsidian(readme = readme,caminho_docs:Path | str = PASTA_DOCS_VS_CODE,caminho_pro_obsidian: Path | str = PASTA_PROJETO_SENSOR_VIBRAÇÃO_OBSIDAN):
    """
    Copia os arquivos de documentação do projeto para a pasta do Obsidian.
    """

    print(f"Caminho da documentação: {caminho_docs}\n")
    print(f"Caminho do Obsidian: {caminho_pro_obsidian}\n")

    print("Copiando arquivos...")


    if not os.path.exists(caminho_docs):
        print("Caminho de documentação não encontrado:", caminho_docs)
        return

    if not os.path.exists(caminho_pro_obsidian):
        print("Caminho do Obsidian não encontrado:", caminho_pro_obsidian)
        return

    shutil.copy2(readme, caminho_pro_obsidian)
    print(f"Arquivo {readme} copiado para {caminho_pro_obsidian}\n")

    # Copia os arquivos de documentação para a pasta do Obsidian
    shutil.copytree(caminho_docs, caminho_pro_obsidian, dirs_exist_ok=True,ignore = shutil.ignore_patterns(*arquivos_ignorar))
    print(f"Arquivos de {caminho_docs} copiados para {caminho_pro_obsidian}\n")

    time.sleep(1)
    print("Arquivos copiados com sucesso!")

    return

if __name__ == "__main__":
    copia_docs_para_obsidian()
    

