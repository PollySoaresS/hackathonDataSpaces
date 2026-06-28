# Capa de infraestructura legacy — ALBA data_IA
# ─────────────────────────────────────────────────────────────────────────────
# NOTA ARQUITECTURAL: estos módulos son adaptadores de infraestructura
# (clientes HTTP hacia Groq, HuggingFace, DeepSeek, VRP).
# Son consumidos ÚNICAMENTE por app/infrastructure/adapters/.
# No importar directamente desde routes/ ni use_cases/.
# Ruta canónica hexagonal: routes → use_cases → services(app) → adapters → [aquí]
