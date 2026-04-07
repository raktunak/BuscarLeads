---
name: Sincronizar memoria con carpeta espejo
description: Cada vez que se cree o modifique un archivo de memoria, copiar tambien a .claude-mirror/ en el repo
type: feedback
---

Siempre que se cree o modifique un archivo en la memoria de Claude (C:\Users\raktu\.claude\projects\c--VenderWEB\memory\), se debe copiar automaticamente a c:/VenderWEB/.claude-mirror/memory/. Lo mismo aplica para planes (.claude-mirror/plans/).

**Why:** El usuario quiere tener una copia versionada de todo el contexto de Claude dentro del repositorio, para poder compartirlo o recuperarlo.

**How to apply:** Tras cada escritura o edicion de un archivo de memoria o plan, ejecutar un cp al directorio .claude-mirror/ correspondiente en el repo. Esto es obligatorio, no opcional.
