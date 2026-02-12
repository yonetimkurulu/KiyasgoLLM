"""
Multi-Agent Jury Evaluation System
===================================
Uc farkli uzman alt-ajan profili uzerinden KiyasGO AI cekirdegini degerlendirir.
Her ajan bagimsiz bir "Dusunce Yolu" (Reasoning Path) olusturur,
sonra argumanlari algoritmik olarak carpistirir ve nihai skor belirlenir.
Son olarak Refleksif Analiz ile kendi kararini elestirir.
"""
import asyncio
import json
import sys
import os
import time
from dataclasses import dataclass, field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.llm import LLMProvider

# ============================================================
# 1. SUB-AGENT PROFILES
# ============================================================

@dataclass
class ReasoningNode:
    """A single node in the Tree of Thoughts."""
    thought: str
    score: float  # 0-10
    children: list = field(default_factory=list)
    is_dead_end: bool = False
    backtrack_reason: str = ""

@dataclass
class AgentVerdict:
    """Final verdict from one sub-agent."""
    agent_name: str
    role: str
    reasoning_tree: list[ReasoningNode]
    final_score: float
    findings: list[str]
    recommendations: list[str]


AGENT_PROFILES = {
    "syntactic_logician": {
        "name": "Kati Sentaktik Mantikci",
        "role": "Sadece kodun ve ciktinin deterministik dogruluguna ve syntax kurallarina bakar.",
        "system_prompt": """Sen bir Kati Sentaktik Mantikci'sin.
Gorevlerin:
1. Kodun deterministik dogrulugunu degerlendir.
2. Syntax hatalarini, tip uyumsuzluklarini, eksik import'lari tespit et.
3. Pydantic model tutarliligini kontrol et: Field tipleri, default degerler, ge/le constraint'leri.
4. Async/await kullanim tutarliligini dogrula.
5. Edge-case'lerde (None input, bos liste, 0 deger) kodun kirilip kirilmayacagini analiz et.
6. JSON parse guvenliligi: LLM ciktisi bozuk JSON donerse ne olur?

Puanlama Kriterleri (0-10):
- 10: Sifir hata, tum edge-case'ler ele alinmis
- 7-9: Kucuk uyarilar var ama kritik degil
- 4-6: Bazi edge-case'ler kacirilmis, production'da sorun cikarabilir
- 1-3: Ciddi syntax/mantik hatalari var

Dusunerek ilerle. Her bulguyu ayri bir "dusunce dugumu" olarak isle.
Bir dal cikmaza girerse, o dali terk et ve alternatif degerlendir.

CIKTINI ASAGIDAKI JSON FORMATINDA VER:
{
  "reasoning_nodes": [
    {"thought": "...", "score": 0.0, "is_dead_end": false, "backtrack_reason": ""},
    ...
  ],
  "final_score": 0.0,
  "findings": ["Bulgu 1", "Bulgu 2", ...],
  "recommendations": ["Oneri 1", "Oneri 2", ...]
}
Sadece JSON dondur.""",
    },
    "security_hallucination_auditor": {
        "name": "Guvenlik ve Yanilsama Denetcisi",
        "role": "Ciktida mantiksal atlama, halucinasyon veya guvenlik zafiyeti arar.",
        "system_prompt": """Sen bir Guvenlik ve Yanilsama (Hallucination) Denetcisi'sin.
Gorevlerin:
1. LLM ciktisinda halucinasyon kontrolu: Uydurma ozellik, yanlis teknik bilgi, olmayan karsilastirma.
2. Prompt injection zafiyeti: Kullanici girdisi LLM prompt'una dogrudan enjekte ediliyor mu?
3. Veri sizintisi riski: API key, ic yapi bilgisi, hassas veri ifsa riski var mi?
4. Mock veri guvenliligi: Mock data production'a kacar mi?
5. Fallback mekanizmasi guvenliligi: Mock response gercek bir analizmis gibi sunuluyor mu?
6. Mantiksal atlama: best_for puanlari ile who_should_buy arasinda tutarsizlik var mi?

Puanlama Kriterleri (0-10):
- 10: Sifir zafiyet, sifir halucinasyon riski
- 7-9: Minor riskler var ama exploit edilmesi zor
- 4-6: Bazi zafiyetler acik, halucinasyon riski mevcut
- 1-3: Kritik guvenlik aciklari veya ciddi halucinasyon kanallari

Dusunerek ilerle. Her bulguyu ayri bir "dusunce dugumu" olarak isle.

CIKTINI ASAGIDAKI JSON FORMATINDA VER:
{
  "reasoning_nodes": [
    {"thought": "...", "score": 0.0, "is_dead_end": false, "backtrack_reason": ""},
    ...
  ],
  "final_score": 0.0,
  "findings": ["Bulgu 1", ...],
  "recommendations": ["Oneri 1", ...]
}
Sadece JSON dondur.""",
    },
    "skeptical_architect": {
        "name": "Supheci Sistem Mimari",
        "role": "Cozumun uzun vadeli verimliligini ve optimizasyonunu sorgular.",
        "system_prompt": """Sen bir Supheci Sistem Mimari'sin.
Gorevlerin:
1. Mimari tutarlilik: PIE -> Normalizer -> UsageInference -> DecisionSynthesizer pipeline'i optimal mi?
2. Performans: Her urun analizi icin LLM cagrisi gerekli mi? Cache stratejisi yeterli mi?
3. Olceklenebilirlik: 1000 esanlik urun analizi yapilsa sistem nasil davranir?
4. Bagimllik yonetimi: Groq/OpenAI/Ollama fallback zinciri saglam mi?
5. Teknik borc: Mock data, hardcoded degerler, tekrarlayan kodlar.
6. Test edilebilirlik: Unit test yazmak ne kadar kolay?
7. API tasarimi: Endpoint'ler RESTful standartlara uygun mu?

Puanlama Kriterleri (0-10):
- 10: Production-ready, olceklenebilir, optimize
- 7-9: Iyi mimari, bazi optimizasyon firsatlari
- 4-6: Calisiyor ama uzun vadede sorun cikarabilir
- 1-3: Ciddi mimari problemler, yeniden tasarim gerekli

Dusunerek ilerle. Bir dal cikmaza girerse, o dali terk et ve alternatif degerlendir.

CIKTINI ASAGIDAKI JSON FORMATINDA VER:
{
  "reasoning_nodes": [
    {"thought": "...", "score": 0.0, "is_dead_end": false, "backtrack_reason": ""},
    ...
  ],
  "final_score": 0.0,
  "findings": ["Bulgu 1", ...],
  "recommendations": ["Oneri 1", ...]
}
Sadece JSON dondur.""",
    },
}

# ============================================================
# 2. TREE OF THOUGHTS ENGINE
# ============================================================

# Per-agent file assignments to stay under token limits
AGENT_FILES = {
    "syntactic_logician": [
        "src/pie/decision_synthesizer.py",
        "src/pie/normalizer.py",
        "src/models/product.py",
    ],
    "security_hallucination_auditor": [
        "src/pie/decision_synthesizer.py",
        "src/llm/prompts.py",
        "src/api/chat.py",
    ],
    "skeptical_architect": [
        "src/pie/engine.py",
        "src/llm/advanced_provider.py",
        "src/api/products.py",
    ],
}


def build_codebase_context(file_list: list[str]) -> str:
    """Build context string from a specific set of files."""
    parts = []
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    for fp in file_list:
        full = os.path.join(base, fp)
        if os.path.exists(full):
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
            parts.append(f"=== {fp} ===\n{content}\n")
    
    return "\n".join(parts)


async def run_agent(llm: LLMProvider, agent_key: str, codebase_context: str) -> AgentVerdict:
    """Run a single sub-agent evaluation with Tree of Thoughts."""
    profile = AGENT_PROFILES[agent_key]
    
    prompt = f"""Asagidaki kod tabanini degerlendir.

{codebase_context}

Yukaridaki dosyalari dikkatlice incele ve detayli analizini JSON olarak ver."""
    
    response = await llm.generate(
        prompt=prompt,
        system_prompt=profile["system_prompt"],
        max_tokens=2048,
        temperature=0.4,
    )
    
    # Parse response
    cleaned = response.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON block
        import re
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                data = json.loads(match.group(0))
            except:
                data = {
                    "reasoning_nodes": [{"thought": "JSON parse hatasi - ham cikti kullaniliyor", "score": 5.0, "is_dead_end": False, "backtrack_reason": ""}],
                    "final_score": 5.0,
                    "findings": [cleaned[:500]],
                    "recommendations": ["LLM ciktisi JSON formatinda degildi."]
                }
        else:
            data = {
                "reasoning_nodes": [{"thought": "JSON parse hatasi", "score": 5.0, "is_dead_end": False, "backtrack_reason": ""}],
                "final_score": 5.0,
                "findings": [cleaned[:500]],
                "recommendations": ["Tekrar dene."]
            }
    
    # Build reasoning nodes
    nodes = []
    for node_data in data.get("reasoning_nodes", []):
        nodes.append(ReasoningNode(
            thought=node_data.get("thought", ""),
            score=float(node_data.get("score", 5.0)),
            is_dead_end=node_data.get("is_dead_end", False),
            backtrack_reason=node_data.get("backtrack_reason", ""),
        ))
    
    return AgentVerdict(
        agent_name=profile["name"],
        role=profile["role"],
        reasoning_tree=nodes,
        final_score=float(data.get("final_score", 5.0)),
        findings=data.get("findings", []),
        recommendations=data.get("recommendations", []),
    )


# ============================================================
# 3. ALGORITHMIC CLASH & SCORING
# ============================================================

def clash_verdicts(verdicts: list[AgentVerdict]) -> dict:
    """Algorithmically clash the three verdicts."""
    scores = [v.final_score for v in verdicts]
    avg = sum(scores) / len(scores)
    
    # Weighted: Security agent's score is weighted more
    weights = {
        "Kati Sentaktik Mantikci": 0.30,
        "Guvenlik ve Yanilsama Denetcisi": 0.40,
        "Supheci Sistem Mimari": 0.30,
    }
    
    weighted_score = sum(
        v.final_score * weights.get(v.agent_name, 0.33)
        for v in verdicts
    )
    
    # Find disagreements (> 2 point spread)
    disagreements = []
    for i, v1 in enumerate(verdicts):
        for j, v2 in enumerate(verdicts):
            if i < j and abs(v1.final_score - v2.final_score) > 2.0:
                disagreements.append({
                    "agents": [v1.agent_name, v2.agent_name],
                    "scores": [v1.final_score, v2.final_score],
                    "spread": abs(v1.final_score - v2.final_score),
                })
    
    # Collect all findings and recommendations
    all_findings = []
    all_recommendations = []
    for v in verdicts:
        for f in v.findings:
            all_findings.append({"agent": v.agent_name, "finding": f})
        for r in v.recommendations:
            all_recommendations.append({"agent": v.agent_name, "recommendation": r})
    
    return {
        "individual_scores": {v.agent_name: v.final_score for v in verdicts},
        "simple_average": round(avg, 1),
        "weighted_score": round(weighted_score, 1),
        "disagreements": disagreements,
        "all_findings": all_findings,
        "all_recommendations": all_recommendations,
    }


# ============================================================
# 4. REFLEXION (SELF-CRITIQUE)
# ============================================================

async def reflexion(llm: LLMProvider, clash_result: dict) -> dict:
    """Self-critique the evaluation before finalizing."""
    
    prompt = f"""Sen bir ust-duzey AI degerlendirme hakemisin.
Asagida uc farkli uzman ajanin bir kod tabani hakkindaki degerlendirmesinin ozeti var.

JURI SONUCLARI:
{json.dumps(clash_result, ensure_ascii=False, indent=2)}

GOREV:
Kendi degerlendirmeni acimasizca elestir. Su sorulari cevapla:

1. Bu puanlamada gozden kacirilan bir kor nokta var mi?
2. Tekrarlayan bir degerlendirme hatasi yapilmis olabilir mi?
3. Agirliklandirma adil mi?
4. Hangi ajanin argumani en guclu, hangisi en zayif?
5. Gelecekte bu tur degerlendirmelerde kullanilmak uzere 3-5 yeni rubrik kurali olustur.

CIKTINI JSON FORMATINDA VER:
{{
  "blind_spots": ["Kor nokta 1", ...],
  "systematic_errors": ["Hata 1", ...],
  "strongest_agent": "Ajan adi",
  "weakest_agent": "Ajan adi",
  "fairness_assessment": "Adillik degerlendirmesi",
  "adjusted_score": 0.0,
  "new_rubric_rules": [
    {{"rule": "Kural aciklamasi", "category": "syntax|security|architecture", "importance": "critical|high|medium"}},
    ...
  ]
}}
Sadece JSON dondur."""
    
    response = await llm.generate(
        prompt=prompt,
        system_prompt="Sen bir ust-duzey AI degerlendirme hakemisin. Turkce yanit ver. Sadece JSON dondur.",
        max_tokens=2048,
        temperature=0.3,
    )
    
    cleaned = response.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except:
        import re
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        return {
            "blind_spots": ["Reflexion JSON parse hatasi"],
            "adjusted_score": clash_result["weighted_score"],
            "new_rubric_rules": [],
        }


# ============================================================
# 5. MAIN ORCHESTRATOR
# ============================================================

async def main():
    print("=" * 60)
    print("  KIYASGO AI - COKLU-AJAN JURI DEGERLENDIRMESI")
    print("=" * 60)
    
    llm = LLMProvider()
    
    # Build codebase context
    print("\n[1/5] Kod tabani analiz icin hazirlaniyor...")
    print(f"      -> Dosyalar ajan bazinda yuklenecek.")
    
    # Run all 3 agents with their own file context
    print("\n[2/5] Uzman ajanlar bagimsiz olarak degerlendirme yapiyor...")
    agent_keys = list(AGENT_PROFILES.keys())
    
    verdicts = []
    for key in agent_keys:
        profile = AGENT_PROFILES[key]
        agent_context = build_codebase_context(AGENT_FILES[key])
        print(f"      -> {profile['name']} calisiyor... ({len(agent_context)} karakter)")
        verdict = await run_agent(llm, key, agent_context)
        verdicts.append(verdict)
        print(f"         Skor: {verdict.final_score}/10 | Bulgular: {len(verdict.findings)}")
        # Rate limit cushion
        await asyncio.sleep(2)
    
    # Algorithmic Clash
    print("\n[3/5] Argumanlari algoritmik olarak carpiştiriliyor...")
    clash_result = clash_verdicts(verdicts)
    print(f"      -> Basit Ortalama: {clash_result['simple_average']}/10")
    print(f"      -> Agirlikli Skor: {clash_result['weighted_score']}/10")
    if clash_result["disagreements"]:
        print(f"      -> Celiski Sayisi: {len(clash_result['disagreements'])}")
    
    # Reflexion
    print("\n[4/5] Refleksif Analiz: Kendi karari elestiriliyor...")
    reflexion_result = await reflexion(llm, clash_result)
    adjusted = reflexion_result.get("adjusted_score", clash_result["weighted_score"])
    print(f"      -> Duzeltilmis Skor: {adjusted}/10")
    print(f"      -> Kor Noktalar: {len(reflexion_result.get('blind_spots', []))}")
    print(f"      -> Yeni Kurallar: {len(reflexion_result.get('new_rubric_rules', []))}")
    
    # Save results
    print("\n[5/5] Sonuclar kaydediliyor...")
    
    full_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "verdicts": [],
        "clash": clash_result,
        "reflexion": reflexion_result,
        "final_score": adjusted,
    }
    
    for v in verdicts:
        full_report["verdicts"].append({
            "agent_name": v.agent_name,
            "role": v.role,
            "final_score": v.final_score,
            "reasoning_tree": [
                {
                    "thought": n.thought,
                    "score": n.score,
                    "is_dead_end": n.is_dead_end,
                    "backtrack_reason": n.backtrack_reason
                }
                for n in v.reasoning_tree
            ],
            "findings": v.findings,
            "recommendations": v.recommendations,
        })
    
    # Save JSON report
    report_path = os.path.join(os.path.dirname(__file__), "jury_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)
    print(f"      -> JSON rapor: {report_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("  NIHAI SONUC")
    print("=" * 60)
    for v in verdicts:
        bar = "#" * int(v.final_score)
        print(f"  {v.agent_name:40s} | {v.final_score:4.1f}/10 | {bar}")
    print(f"  {'---':40s} | {'---':>4s} |")
    print(f"  {'AGIRLIKLI SKOR':40s} | {clash_result['weighted_score']:4.1f}/10 |")
    print(f"  {'DUZELTILMIS SKOR (REFLEXION)':40s} | {adjusted:4.1f}/10 |")
    print("=" * 60)
    
    return full_report


if __name__ == "__main__":
    report = asyncio.run(main())
