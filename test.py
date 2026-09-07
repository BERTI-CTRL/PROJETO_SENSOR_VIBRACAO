from pathlib import Path

pasta = Path(r"G:\Meu Drive\Obsidian")

print("Existe?", pasta.exists())
print("É pasta?", pasta.is_dir())
print("Caminho:", pasta)