"""Conservative, explainable requirement mapping. Scores are not hiring probabilities."""

import re

TECHNOLOGIES = (
    "python",
    "sql",
    "rag",
    "llm",
    "langchain",
    "faiss",
    "chroma",
    "pytorch",
    "tensorflow",
    "docker",
    "kubernetes",
    "azure",
    "aws",
    "power bi",
    "power apps",
    "power automate",
    "copilot studio",
    "sharepoint",
    "fastapi",
    "etl",
    "n8n",
)


def contains(text, term):
    return bool(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.I))


def requirement_map(opportunity, facts):
    if opportunity.kind == "speculative":
        return {
            "method": "speculative_role_coverage_only",
            "requirements": [],
            "coverage": None,
            "note": "No published vacancy requirements are asserted.",
        }
    sentences = re.split(r"[\n.!?]+", opportunity.description)
    requirements = []
    for term in TECHNOLOGIES:
        quotes = [s.strip() for s in sentences if contains(s, term)]
        if not quotes:
            continue
        evidence = [f.id for f in facts if contains(f.text, term)]
        mandatory = any(
            re.search(r"\b(must|required|essential|mandatory|zorunlu)\b", q, re.I) for q in quotes
        )
        requirements.append(
            {
                "skill": term,
                "source_url": opportunity.source_url,
                "source_quote": quotes[0],
                "importance": "required" if mandatory else "mentioned",
                "approved_fact_ids": evidence,
                "status": "supported" if evidence else "gap",
            }
        )
    coverage = (
        round(100 * sum(bool(r["approved_fact_ids"]) for r in requirements) / len(requirements))
        if requirements
        else None
    )
    return {
        "method": "literal_source_skill_mapping_v1",
        "requirements": requirements,
        "coverage": coverage,
        "note": "Literal mapping cannot infer experience depth or work rights; review the original requirements.",
    }
