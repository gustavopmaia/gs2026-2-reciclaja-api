"""Base oficial de orientação de descarte (fonte de verdade do domínio).

O LLM só reescreve isto em linguagem natural; o fallback usa este texto direto.
Textos resumidos a partir das orientações públicas de coleta seletiva (PNRS, Lei 12.305/2010).
"""

from __future__ import annotations

import re
import unicodedata

from domain.models import Material

GUIDANCE: dict[Material, str] = {
    Material.PAPEL: "Papel e papelão vão limpos e secos, desmontados. Papel engordurado ou papel higiênico não é reciclável.",
    Material.PLASTICO: "Embalagens plásticas vão vazias e enxaguadas. Tampas podem ir junto. Isopor sujo vai no lixo comum.",
    Material.VIDRO: "Vidro vai inteiro ou embrulhado em jornal, sem tampa. Espelho e vidro temperado não entram na coleta comum.",
    Material.METAL: "Latas de alumínio e aço vão vazias e amassadas. Latas de tinta ou aerossol cheias são resíduo perigoso.",
    Material.ELETRONICO: "Eletroeletrônicos vão inteiros, sem pilhas, para ecoponto ou ponto de logística reversa. Apague seus dados antes.",
    Material.PILHA_BATERIA: "Pilhas e baterias nunca vão no lixo comum: leve a um ponto de logística reversa (ecoponto ou comércio participante).",
    Material.OLEO_COZINHA: "Óleo de cozinha usado vai frio, em garrafa PET fechada. Nunca jogue na pia: 1 litro contamina milhares de litros de água.",
    Material.LAMPADA: "Lâmpadas fluorescentes contêm mercúrio: leve inteiras, embaladas, a um ponto de logística reversa. Não quebre.",
    Material.VOLUMOSO: "Móveis e colchões vão para ecoponto (até 1 m³ por dia) ou pelo agendamento de cata-bagulho da prefeitura.",
    Material.ENTULHO: "Entulho de pequenas obras vai para ecoponto (até 1 m³ por dia). Acima disso, contrate caçamba licenciada.",
}

# Palavra-chave (sem acento, minúscula) -> material. Ordem importa: termos mais específicos primeiro.
KEYWORDS: list[tuple[str, Material]] = [
    ("oleo", Material.OLEO_COZINHA),
    ("pilha", Material.PILHA_BATERIA),
    ("bateria", Material.PILHA_BATERIA),
    ("lampada", Material.LAMPADA),
    ("celular", Material.ELETRONICO),
    ("computador", Material.ELETRONICO),
    ("notebook", Material.ELETRONICO),
    ("eletronico", Material.ELETRONICO),
    ("eletrodomestico", Material.ELETRONICO),
    ("televis", Material.ELETRONICO),
    ("geladeira", Material.VOLUMOSO),
    ("sofa", Material.VOLUMOSO),
    ("colchao", Material.VOLUMOSO),
    ("movel", Material.VOLUMOSO),
    ("moveis", Material.VOLUMOSO),
    ("entulho", Material.ENTULHO),
    ("tijolo", Material.ENTULHO),
    ("cimento", Material.ENTULHO),
    ("azulejo", Material.ENTULHO),
    ("vidro", Material.VIDRO),
    ("garrafa de vinho", Material.VIDRO),
    ("pote de vidro", Material.VIDRO),
    ("lata", Material.METAL),
    ("aluminio", Material.METAL),
    ("metal", Material.METAL),
    ("pet", Material.PLASTICO),
    ("plastic", Material.PLASTICO),
    ("sacola", Material.PLASTICO),
    ("papelao", Material.PAPEL),
    ("papel", Material.PAPEL),
    ("jornal", Material.PAPEL),
    ("caixa", Material.PAPEL),
]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def detect_material(text: str) -> Material | None:
    norm = normalize(text)
    for keyword, material in KEYWORDS:
        # \b no início evita falso positivo ("carpete" não é "pet").
        if re.search(r"\b" + re.escape(keyword), norm):
            return material
    return None
