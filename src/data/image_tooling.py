"""
Image Dataset Tooling and Synthetic Receipt Generator.
Generates realistic SME document images (receipts, invoices, bills) across
English, Bengali, and Mixed bilingual text with ground-truth bounding-box annotations.
Exports standard COCO / JSON metadata for OCR and layout model training.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from src.config import settings


class DocumentImageDatasetTooling:
    """Manages synthetic image creation, augmentation metadata, and annotation schemas."""

    DISTRIBUTION_TARGETS = {
        "sales_receipt": 2000,
        "purchase_invoice": 1500,
        "expense_receipt": 1000,
        "payment_receipt": 500,
    }

    LANGUAGES = ["en", "bn", "bn_en"]

    @classmethod
    def generate_receipt_image(
        cls,
        image_id: int,
        doc_class: str,
        language: str = "en",
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Renders a synthetic thermal/POS receipt or invoice image.
        Returns complete metadata schema with ground-truth fields and text regions.
        """
        output_dir = output_dir or settings.STORAGE_DIR / "synthetic_images"
        output_dir.mkdir(parents=True, exist_ok=True)

        width, height = 450, 650
        # Background: subtle aged off-white / light cream paper
        bg_color = (250, 249, 246)
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Default standard fonts or fallbacks
        try:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
        except Exception:
            font_title = None
            font_body = None

        text_color = (30, 30, 30)

        # Header Titles based on language and class
        if doc_class == "sales_receipt":
            title = "CASH MEMO" if language == "en" else ("ক্যাশ মেমো" if language == "bn" else "CASH MEMO / ক্যাশ মেমো")
            vendor = "Al-Madina General Store" if language != "bn" else "আল-মদিনা জেনারেল স্টোর"
        elif doc_class == "purchase_invoice":
            title = "SUPPLIER INVOICE" if language == "en" else ("সরবরাহ চালান" if language == "bn" else "CHALLAN / চালান")
            vendor = "Pran Agro Distributorship Ltd"
        elif doc_class == "expense_receipt":
            title = "EXPENSE VOUCHER" if language == "en" else ("খরচ ভাউচার" if language == "bn" else "EXPENSE / ভাউচার")
            vendor = "Commercial Premises Office"
        else:
            title = "PAYMENT RECEIPT" if language == "en" else ("টাকা প্রাপ্তি রসিদ" if language == "bn" else "PAYMENT / রসিদ")
            vendor = "SME Counter Collection"

        inv_number = f"REC-{image_id:05d}"
        date_str = f"2026-10-{random.randint(1, 28):02d}"

        # Draw Header
        y = 30
        draw.text((width // 2 - 80, y), title, fill=text_color, font=font_title)
        y += 30
        draw.text((width // 2 - 90, y), vendor, fill=(70, 70, 70), font=font_body)
        y += 25
        draw.line([(30, y), (width - 30, y)], fill=(180, 180, 180), width=1)
        y += 15

        # Metadata lines
        draw.text((35, y), f"Invoice #: {inv_number}", fill=text_color, font=font_body)
        draw.text((width - 150, y), f"Date: {date_str}", fill=text_color, font=font_body)
        y += 25
        draw.line([(30, y), (width - 30, y)], fill=(200, 200, 200), width=1)
        y += 15

        # Sample Line Items
        items_meta = []
        subtotal = 0
        sample_items = [
            ("Miniket Rice 5kg", 1, 38000),
            ("Soybean Oil 1L", 2, 18500),
            ("Teer Sugar 1kg", 2, 13000),
            ("Aarong Milk 500ml", 1, 4500),
        ]
        num_items = random.randint(2, 4)

        for i in range(num_items):
            desc, qty, unit_price = sample_items[i % len(sample_items)]
            line_tot = qty * unit_price
            subtotal += line_tot

            item_text = f"{desc} x{qty}"
            price_text = f"BDT {line_tot / 100:.2f}"
            draw.text((35, y), item_text, fill=text_color, font=font_body)
            draw.text((width - 140, y), price_text, fill=text_color, font=font_body)

            items_meta.append({
                "description": desc,
                "quantity": qty,
                "unit_price_minor": unit_price,
                "line_total_minor": line_tot,
                "bbox": [35, y, width - 35, y + 16],
            })
            y += 24

        y += 10
        draw.line([(30, y), (width - 30, y)], fill=(180, 180, 180), width=1)
        y += 15

        # Totals
        draw.text((width - 240, y), "Subtotal:", fill=text_color, font=font_body)
        draw.text((width - 140, y), f"BDT {subtotal / 100:.2f}", fill=text_color, font=font_body)
        y += 24
        draw.text((width - 240, y), "TOTAL:", fill=(10, 10, 10), font=font_title)
        draw.text((width - 140, y), f"BDT {subtotal / 100:.2f}", fill=(10, 10, 10), font=font_title)
        y += 40

        # Footer
        draw.text((width // 2 - 75, y), "Thank You for Your Business!", fill=(100, 100, 100), font=font_body)

        # Save image file
        file_name = f"doc_{doc_class}_{language}_{image_id:05d}.png"
        img_path = output_dir / file_name
        img.save(img_path)

        # Partition Split (70% train, 15% val, 15% test)
        rnd_split = random.random()
        if rnd_split < 0.70:
            split = "train"
        elif rnd_split < 0.85:
            split = "val"
        else:
            split = "test"

        metadata = {
            "image_id": image_id,
            "document_class": doc_class,
            "language": language,
            "image_filename": file_name,
            "image_path": str(img_path),
            "width": width,
            "height": height,
            "split": split,
            "provenance": "synthetic",
            "quality": {
                "rotation_deg": 0.0,
                "blur_score": 0.0,
                "lighting": "uniform",
                "handwriting_present": False,
            },
            "ground_truth": {
                "document_title": title,
                "vendor_name": vendor,
                "invoice_number": inv_number,
                "date": date_str,
                "subtotal_minor": subtotal,
                "total_minor": subtotal,
                "items": items_meta,
            },
        }

        return metadata

    @classmethod
    def generate_sample_collection(cls, count: int = 20) -> Path:
        """
        Generates a sample batch of synthetic documents and exports full metadata JSON.
        """
        out_dir = settings.STORAGE_DIR / "synthetic_images"
        out_dir.mkdir(parents=True, exist_ok=True)

        metadata_records = []
        classes = list(cls.DISTRIBUTION_TARGETS.keys())

        for i in range(1, count + 1):
            doc_class = classes[i % len(classes)]
            lang = cls.LANGUAGES[i % len(cls.LANGUAGES)]
            meta = cls.generate_receipt_image(image_id=i, doc_class=doc_class, language=lang, output_dir=out_dir)
            metadata_records.append(meta)

        index_file = out_dir / "dataset_manifest.json"
        index_file.write_text(json.dumps(metadata_records, indent=2), encoding="utf-8")
        print(f"Generated {count} synthetic document samples and manifest at {index_file}")
        return index_file


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Synthetic Document Image Generator Tooling")
    parser.add_argument("--count", type=int, default=20, help="Number of sample images to generate")
    args = parser.parse_args()
    DocumentImageDatasetTooling.generate_sample_collection(count=args.count)
