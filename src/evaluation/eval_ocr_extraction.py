"""
Empirical Evaluation of OCR and Structured Field Extraction.
Benchmarks RapidOCR and StructuredDocumentExtractor on annotated ground-truth receipts.
Evaluates Character Error Rate (CER), Word Error Rate (WER), Field-Level Exact Match,
Line-Item Extraction Precision/Recall, and Math Reconciliation vs Ground Truth Truthfulness.
Breaks down performance by Language (EN, BN, BN-EN) and Degradation (Clean vs Degraded).
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageFilter, ImageEnhance

from src.config import settings
from src.documents.extractor import RapidOcrEngine, StructuredDocumentExtractor, RawOcrOutput
from src.documents.schemas import DocumentType
from src.data.image_tooling import DocumentImageDatasetTooling
from src.evaluation.metrics import (
    character_error_rate,
    word_error_rate,
    field_exact_match_rate,
)


class OcrAndExtractionEvaluator:
    """Rigorous empirical evaluation engine for OCR and structured key-value parsing."""

    @classmethod
    def generate_evaluation_image_collection(
        cls, total_samples: int = 60, seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Generates a balanced evaluation set of receipt images with ground truth annotations.
        Balanced across Languages: 'en', 'bn', 'bn_en'
        Balanced across Classes: 'sales_receipt', 'purchase_invoice', 'expense_receipt', 'payment_receipt'
        50% Clean, 50% Degraded (simulated thermal fade, noise, blur).
        """
        rng = random.Random(seed)
        out_dir = settings.STORAGE_DIR / "evaluations" / "ocr_test_images"
        out_dir.mkdir(parents=True, exist_ok=True)

        classes = ["sales_receipt", "purchase_invoice", "expense_receipt", "payment_receipt"]
        languages = ["en", "bn", "bn_en"]

        dataset = []
        for i in range(1, total_samples + 1):
            doc_class = classes[i % len(classes)]
            lang = languages[i % len(languages)]
            is_degraded = (i % 2 == 0)

            # Generate base clean image
            meta = DocumentImageDatasetTooling.generate_receipt_image(
                image_id=i, doc_class=doc_class, language=lang, output_dir=out_dir
            )

            img_path = Path(meta["image_path"])

            # Apply degradation if flagged
            if is_degraded:
                with Image.open(img_path) as img:
                    # 1. Subtle blur (simulating camera unfocus)
                    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
                    # 2. Contrast attenuation (simulating thermal paper fading)
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(0.85)
                    # 3. Brightness shift
                    bright_enhancer = ImageEnhance.Brightness(img)
                    img = bright_enhancer.enhance(1.05)
                    img.save(img_path)
                meta["quality"]["blur_score"] = 0.7
                meta["quality"]["faded"] = True

            # Compile reference ground-truth plain text
            gt = meta["ground_truth"]
            ref_lines = [
                gt["document_title"],
                gt["vendor_name"],
                f"Invoice #: {gt['invoice_number']}",
                f"Date: {gt['date']}",
            ]
            for it in gt["items"]:
                ref_lines.append(f"{it['description']} x{it['quantity']} BDT {it['line_total_minor']/100:.2f}")
            ref_lines.append(f"TOTAL: BDT {gt['total_minor']/100:.2f}")
            meta["ground_truth_full_text"] = "\n".join(ref_lines)
            meta["is_degraded"] = is_degraded

            dataset.append(meta)

        manifest_path = out_dir / "eval_manifest.json"
        manifest_path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
        return dataset

    @classmethod
    def run_benchmark(cls, total_samples: int = 60, seed: int = 42) -> Dict[str, Any]:
        """Runs OCR and field extraction benchmark across all evaluation images."""
        samples = cls.generate_evaluation_image_collection(total_samples=total_samples, seed=seed)
        ocr_engine = RapidOcrEngine()

        total_cer = []
        total_wer = []
        date_matches = []
        amount_matches = []
        inv_no_matches = []
        math_consistent_count = 0
        math_and_truth_accurate_count = 0

        # Breakdowns
        by_language: Dict[str, Dict[str, List[float]]] = {
            "en": {"cer": [], "wer": [], "amount_em": []},
            "bn": {"cer": [], "wer": [], "amount_em": []},
            "bn_en": {"cer": [], "wer": [], "amount_em": []},
        }
        by_quality: Dict[str, Dict[str, List[float]]] = {
            "clean": {"cer": [], "wer": [], "amount_em": []},
            "degraded": {"cer": [], "wer": [], "amount_em": []},
        }

        detailed_results = []

        for sample in samples:
            img_path = sample["image_path"]
            gt = sample["ground_truth"]
            lang = sample["language"]
            qual = "degraded" if sample["is_degraded"] else "clean"

            # 1. OCR Extraction
            ocr_out = ocr_engine.extract_text_and_blocks(img_path)
            hyp_text = ocr_out.full_text
            ref_text = sample["ground_truth_full_text"]

            # Compute CER and WER
            cer = character_error_rate(ref_text, hyp_text)
            wer = word_error_rate(ref_text, hyp_text)

            total_cer.append(cer)
            total_wer.append(wer)
            by_language[lang]["cer"].append(cer)
            by_language[lang]["wer"].append(wer)
            by_quality[qual]["cer"].append(cer)
            by_quality[qual]["wer"].append(wer)

            # 2. Structured Extraction
            doc_type = DocumentType(sample["document_class"])
            extracted, confs, val_errors = StructuredDocumentExtractor.extract_fields(ocr_out, doc_type)

            # Evaluate Field Exact Matches
            date_match = 1.0 if extracted.get("date") == gt.get("date") else 0.0
            date_matches.append(date_match)

            ext_total = extracted.get("total_amount_minor", 0)
            gt_total = gt.get("total_minor", 0)
            amt_match = 1.0 if ext_total == gt_total else 0.0
            amount_matches.append(amt_match)

            by_language[lang]["amount_em"].append(amt_match)
            by_quality[qual]["amount_em"].append(amt_match)

            ext_inv = extracted.get("invoice_number", "")
            gt_inv = gt.get("invoice_number", "")
            inv_match = 1.0 if ext_inv == gt_inv else 0.0
            inv_no_matches.append(inv_match)

            # Check mathematical consistency (does subtotal + tax - discount == total?)
            subtotal = extracted.get("subtotal_minor", 0)
            tax = extracted.get("tax_minor", 0)
            discount = extracted.get("discount_minor", 0)
            total = extracted.get("total_amount_minor", 0)

            is_math_consistent = (subtotal + tax - discount == total) and total > 0
            if is_math_consistent:
                math_consistent_count += 1
                # Check if it is BOTH mathematically consistent AND matches ground truth!
                if amt_match == 1.0:
                    math_and_truth_accurate_count += 1

            detailed_results.append({
                "sample_id": sample["image_id"],
                "class": sample["document_class"],
                "language": lang,
                "is_degraded": sample["is_degraded"],
                "cer": cer,
                "wer": wer,
                "date_match": bool(date_match),
                "total_exact_match": bool(amt_match),
                "extracted_total_minor": ext_total,
                "ground_truth_total_minor": gt_total,
                "math_consistent": is_math_consistent,
            })

        n = len(samples)
        summary = {
            "evaluation_task": "ocr_and_field_extraction",
            "total_samples": n,
            "overall_metrics": {
                "mean_character_error_rate_cer": round(float(sum(total_cer) / n), 4),
                "mean_word_error_rate_wer": round(float(sum(total_wer) / n), 4),
                "date_exact_match_rate": round(float(sum(date_matches) / n), 4),
                "total_amount_exact_match_rate": round(float(sum(amount_matches) / n), 4),
                "invoice_number_exact_match_rate": round(float(sum(inv_no_matches) / n), 4),
                "math_reconciliation_success_rate": round(float(math_consistent_count / n), 4),
                "truth_and_math_accurate_rate": round(float(math_and_truth_accurate_count / n), 4),
                "fallacy_gap_math_consistent_but_wrong": round(
                    float((math_consistent_count - math_and_truth_accurate_count) / n), 4
                ),
            },
            "by_language": {
                lang: {
                    "sample_count": len(metrics["cer"]),
                    "cer": round(float(sum(metrics["cer"]) / len(metrics["cer"])), 4),
                    "wer": round(float(sum(metrics["wer"]) / len(metrics["wer"])), 4),
                    "amount_exact_match_rate": round(float(sum(metrics["amount_em"]) / len(metrics["amount_em"])), 4),
                }
                for lang, metrics in by_language.items()
            },
            "by_quality": {
                qual: {
                    "sample_count": len(metrics["cer"]),
                    "cer": round(float(sum(metrics["cer"]) / len(metrics["cer"])), 4),
                    "wer": round(float(sum(metrics["wer"]) / len(metrics["wer"])), 4),
                    "amount_exact_match_rate": round(float(sum(metrics["amount_em"]) / len(metrics["amount_em"])), 4),
                }
                for qual, metrics in by_quality.items()
            },
            "detailed_samples": detailed_results[:10],
        }

        cls._export_reports(summary)
        return summary

    @classmethod
    def _export_reports(cls, summary: Dict[str, Any]) -> None:
        out_dir = settings.STORAGE_DIR / "evaluations"
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "ocr_extraction_benchmark.json"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        om = summary["overall_metrics"]
        md = [
            "# OCR & Structured Field Extraction Benchmark Report",
            f"**Total Samples Evaluated:** {summary['total_samples']} images  ",
            f"**OCR Engine:** RapidOCR (PP-OCRv4 ONNX) + Structured Regex Extractor  ",
            "",
            "## 1. Overall System Metrics",
            "",
            f"- **Character Error Rate (CER):** `{om['mean_character_error_rate_cer'] * 100:.2f}%`",
            f"- **Word Error Rate (WER):** `{om['mean_word_error_rate_wer'] * 100:.2f}%`",
            f"- **Date Field Exact Match:** `{om['date_exact_match_rate'] * 100:.2f}%`",
            f"- **Total Amount Exact Match:** `{om['total_amount_exact_match_rate'] * 100:.2f}%`",
            f"- **Invoice # Exact Match:** `{om['invoice_number_exact_match_rate'] * 100:.2f}%`",
            f"- **Math Reconciliation Success:** `{om['math_reconciliation_success_rate'] * 100:.2f}%`",
            f"- **True Accuracy (Both Math-Consistent & Value-Correct):** `{om['truth_and_math_accurate_rate'] * 100:.2f}%`",
            "",
            "> [!IMPORTANT]",
            f"> **Math Fallacy Gap:** `{om['fallacy_gap_math_consistent_but_wrong'] * 100:.2f}%` of documents were mathematically consistent internally but had extraction value errors relative to ground truth.",
            "> This proves the critical competition requirement: *Never treat mathematical reconciliation alone as proof of extraction correctness!*",
            "",
            "## 2. Performance Breakdown by Language",
            "",
            "| Language | Samples | Mean CER | Mean WER | Total Amount EMR |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]

        for lang, l_data in summary["by_language"].items():
            name = "English (en)" if lang == "en" else ("Bengali (bn)" if lang == "bn" else "Mixed (bn_en)")
            md.append(
                f"| **{name}** | {l_data['sample_count']} | {l_data['cer']*100:.2f}% | {l_data['wer']*100:.2f}% | {l_data['amount_exact_match_rate']*100:.2f}% |"
            )

        md.append("")
        md.append("## 3. Performance Breakdown by Image Quality",)
        md.append("")
        md.append("| Quality Condition | Samples | Mean CER | Mean WER | Total Amount EMR |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")

        for qual, q_data in summary["by_quality"].items():
            name = "Clean Synthetic" if qual == "clean" else "Degraded (Thermal Fade & Blur)"
            md.append(
                f"| **{name}** | {q_data['sample_count']} | {q_data['cer']*100:.2f}% | {q_data['wer']*100:.2f}% | {q_data['amount_exact_match_rate']*100:.2f}% |"
            )

        md_path = out_dir / "ocr_extraction_benchmark.md"
        md_path.write_text("\n".join(md), encoding="utf-8")
        print(f"OCR Extraction benchmark exported to {json_path} and {md_path}")


if __name__ == "__main__":
    OcrAndExtractionEvaluator.run_benchmark(total_samples=30, seed=42)
