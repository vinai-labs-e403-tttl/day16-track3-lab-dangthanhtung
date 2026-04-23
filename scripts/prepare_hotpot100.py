from __future__ import annotations

import json
from pathlib import Path

import typer
from datasets import load_dataset

app = typer.Typer(add_completion=False)


@app.command()
def main(out: str = "data/hotpot_100.json", limit: int = 100) -> None:
    dataset = load_dataset(
        "hotpotqa/hotpot_qa",
        "distractor",
        split="validation",
        streaming=True,
    )
    rows: list[dict] = []
    for item in dataset:
        titles = item["context"]["title"]
        sentences = item["context"]["sentences"]
        context = [
            {"title": title, "text": " ".join(sentence_group)}
            for title, sentence_group in zip(titles, sentences)
        ]
        rows.append(
            {
                "qid": item["id"],
                "difficulty": item["level"],
                "question": item["question"],
                "gold_answer": item["answer"],
                "context": context,
            }
        )
        if len(rows) >= limit:
            break

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(f"Wrote {len(rows)} examples to {out_path}")


if __name__ == "__main__":
    app()
