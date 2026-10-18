"""
Scalable Receipt Image Dataset Ingestion and Annotation Builder.
Generates an annotated benchmark corpus of 1,000 synthetic receipt images
(architected to scale toward 5,000) across:
- Languages: English ('en'), Bengali ('bn'), Mixed Bilingual ('bilingual')
- Document Types: Sales Receipt, Purchase Invoice, Expense Receipt, Payment Receipt
- Degradation Categories: Clean, Blur, Rotated, Low Light, Faded Thermal, Shadow, Cropped
Exports per-image annotation JSONs, ground-truth text, bounding boxes, and master manifest.
"""

from __future__ import annotations

import os
import json
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np


class OcrReceiptDatasetBuilder:
    """Renders synthetic thermal receipts and builds independent ground truth annotations."""

    VENDORS_EN = [
        "Desh General Store", "Chowdhury Supermarket", "Bismillah Electronics",
        "Bengal Food Mart", "Rahman Enterprise", "Metro Departmental"
    ]
    VENDORS_BN = [
        "দেশ জেনারেল স্টোর", "চৌধুরী সুপার মার্কেট", "বিসমিল্লাহ ইলেকট্রনিক্স",
        "বেঙ্গল ফুড মার্ট", "রহমান এন্টারপ্রাইজ", "মেট্রো ডিপার্টমেন্টাল"
    ]
    SUPPLIERS = [
        "Abul Khair Consumer Goods Ltd", "Meghna Flour & Edible Oil Mills",
        "Akij Food & Beverage Ltd", "Square Consumer Products Ltd", "Pran-RFL Group"
    ]

    ITEMS_EN = [
        ("Miniket Rice 5kg", 380_00),
        ("Soybean Oil 2L", 360_00),
        ("Refined White Sugar 1kg", 135_00),
        ("Aata Flour 2kg", 110_00),
        ("Masur Dal 1kg", 140_00),
        ("Laundry Soap Bar", 45_00),
        ("Bath Soap 100g", 60_00),
        ("Black Tea Pack 400g", 240_00),
    ]

    ITEMS_BN = [
        ("মিনিকেট চাল ৫ কেজি", 380_00),
        ("সয়াবিন তেল ২ লিটার", 360_00),
        ("সাদা চিনি ১ কেজি", 135_00),
        ("আটা ২ কেজি", 110_00),
        ("মসুর ডাল ১ কেজি", 140_00),
        ("ডিটারজেন্ট সাবান", 45_00),
        ("গোসলের সাবান", 60_00),
        ("চা পাতা ৪০০ গ্রাম", 240_00),
    ]

    DOC_CLASSES = ["sales_receipt", "purchase_invoice", "expense_receipt", "payment_receipt"]
    QUALITY_CATEGORIES = ["clean", "blur", "rotated", "low_light", "faded_thermal", "shadow", "cropped"]
    LANGUAGES = ["en", "bn", "bilingual"]

    @classmethod
    def generate_receipt_image(
        cls,
        image_id: int,
        doc_class: str,
        language: str,
        quality: str,
        output_dir: Path,
        rng: random.Random,
    ) -> Dict[str, Any]:
        """Renders an individual receipt image and returns ground truth annotation."""
        width, height = 480, 680
        bg_color = (252, 250, 246)
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Standard default font
        font = ImageFont.load_default()

        # Vendor & Header Selection
        if language == "en":
            vendor = rng.choice(cls.VENDORS_EN)
            items_pool = cls.ITEMS_EN
            header_map = {
                "sales_receipt": "CASH MEMO / SALES RECEIPT",
                "purchase_invoice": "COMMERCIAL PURCHASE INVOICE",
                "expense_receipt": "PETTY EXPENSE RECEIPT",
                "payment_receipt": "MONEY RECEIPT VOUCHER",
            }
        elif language == "bn":
            vendor = rng.choice(cls.VENDORS_BN)
            items_pool = cls.ITEMS_BN
            header_map = {
                "sales_receipt": "ক্যাশ মেমো / বিক্রয় রসিদ",
                "purchase_invoice": "বাণিজ্যিক ক্রয় চালান",
                "expense_receipt": "দোকান খরচ রসিদ",
                "payment_receipt": "টাকা জমার রসিদ",
            }
        else:  # bilingual
            vendor = f"{rng.choice(cls.VENDORS_EN)} ({rng.choice(cls.VENDORS_BN)})"
            items_pool = cls.ITEMS_EN + cls.ITEMS_BN
            header_map = {
                "sales_receipt": "CASH MEMO (ক্যাশ মেমো)",
                "purchase_invoice": "PURCHASE INVOICE (চালান)",
                "expense_receipt": "EXPENSE VOUCHER (খরচ)",
                "payment_receipt": "MONEY RECEIPT (রসিদ)",
            }

        header_title = header_map[doc_class]
        day = rng.randint(1, 28)
        month = rng.randint(1, 12)
        date_str = f"{day:02d}/{month:02d}/2026"
        inv_no = f"INV-2026-{image_id:04d}"

        # Line items
        num_items = rng.randint(2, 4)
        chosen_items = rng.sample(items_pool, num_items)
        line_items = []
        subtotal_minor = 0

        for name, unit_price in chosen_items:
            qty = rng.randint(1, 3)
            line_tot = qty * unit_price
            subtotal_minor += line_tot
            line_items.append({
                "description": name,
                "quantity": qty,
                "unit_price_minor": unit_price,
                "line_total_minor": line_tot,
            })

        tax_minor = int(round(subtotal_minor * 0.05)) if doc_class in ["sales_receipt", "purchase_invoice"] else 0
        discount_minor = rng.choice([0, 50_00, 100_00]) if subtotal_minor > 500_00 else 0
        total_minor = subtotal_minor + tax_minor - discount_minor

        # Draw text onto image canvas
        text_lines = [
            vendor,
            header_title,
            f"Bill No: {inv_no}",
            f"Date: {date_str}",
            "-" * 42,
        ]

        for itm in line_items:
            text_lines.append(
                f"{itm['description']} x{itm['quantity']}  Tk {(itm['line_total_minor']/100):.2f}"
            )

        text_lines.append("-" * 42)
        text_lines.append(f"Subtotal: Tk {(subtotal_minor/100):.2f}")
        if tax_minor > 0:
            text_lines.append(f"VAT (5%): Tk {(tax_minor/100):.2f}")
        if discount_minor > 0:
            text_lines.append(f"Discount: Tk {(discount_minor/100):.2f}")
        text_lines.append(f"Total Amount: Tk {(total_minor/100):.2f}")
        text_lines.append("=" * 42)
        text_lines.append("Thank you / ধন্যবাদ")

        y_pos = 35
        full_text_gt = "\n".join(text_lines)

        for line in text_lines:
            draw.text((35, y_pos), line, fill=(35, 35, 35), font=font)
            y_pos += 26

        # Apply Physical Degradation
        img = cls._apply_degradation(img, quality, bg_color, rng)

        # Save Image
        img_filename = f"receipt_{image_id:05d}_{language}_{quality}.png"
        img_path = output_dir / img_filename
        img.save(img_path)

        annotation = {
            "image_id": image_id,
            "filename": img_filename,
            "image_path": str(img_path),
            "document_type": doc_class,
            "language": language,
            "quality_category": quality,
            "invoice_number": inv_no,
            "date_str": date_str,
            "line_items": line_items,
            "subtotal_minor": subtotal_minor,
            "tax_minor": tax_minor,
            "discount_minor": discount_minor,
            "total_amount_minor": total_minor,
            "full_text_ground_truth": full_text_gt,
            "is_synthetic": True,
            "provenance": "SME Synthetic Thermal Receipt Generator v2.0",
        }

        return annotation

    @classmethod
    def _apply_degradation(cls, img: Image.Image, quality: str, bg_color: Tuple[int, int, int], rng: random.Random) -> Image.Image:
        """Applies realistic optical and thermal paper distortions."""
        if quality == "blur":
            return img.filter(ImageFilter.GaussianBlur(radius=1.2))

        elif quality == "rotated":
            angle = rng.choice([-4.0, -3.0, 3.0, 4.0])
            return img.rotate(angle, expand=False, fillcolor=bg_color)

        elif quality == "low_light":
            enhancer = ImageEnhance.Brightness(img)
            return enhancer.enhance(0.48)

        elif quality == "faded_thermal":
            # Faded thermal print has lower contrast and grayish ink
            contrast_enhancer = ImageEnhance.Contrast(img)
            img = contrast_enhancer.enhance(0.45)
            brightness_enhancer = ImageEnhance.Brightness(img)
            return brightness_enhancer.enhance(1.15)

        elif quality == "shadow":
            # Add subtle dark shadow gradient across upper half
            shadow_mask = Image.new("L", img.size, color=255)
            draw_mask = ImageDraw.Draw(shadow_mask)
            for y in range(img.height // 2):
                alpha = int(140 + (y / (img.height // 2)) * 115)
                draw_mask.line([(0, y), (img.width, y)], fill=alpha)
            dark_layer = Image.new("RGB", img.size, color=(40, 40, 40))
            return Image.composite(img, dark_layer, shadow_mask)

        elif quality == "cropped":
            # Margins clipped by 25 pixels
            return img.crop((15, 20, img.width - 15, img.height - 20)).resize(img.size)

        return img  # clean


def build_ocr_receipt_dataset(target_count: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """Generates 1,000 annotated receipt images with master manifest."""
    rng = random.Random(seed)
    base_dir = Path("storage/datasets/ocr_receipts")
    img_dir = base_dir / "images"
    ann_dir = base_dir / "annotations"
    img_dir.mkdir(parents=True, exist_ok=True)
    ann_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building {target_count} annotated receipt images in {base_dir}...")
    annotations = []

    doc_classes = OcrReceiptDatasetBuilder.DOC_CLASSES
    languages = OcrReceiptDatasetBuilder.LANGUAGES
    qualities = OcrReceiptDatasetBuilder.QUALITY_CATEGORIES

    for i in range(1, target_count + 1):
        doc_class = doc_classes[i % len(doc_classes)]
        lang = languages[i % len(languages)]
        quality = qualities[i % len(qualities)]

        ann = OcrReceiptDatasetBuilder.generate_receipt_image(
            image_id=i,
            doc_class=doc_class,
            language=lang,
            quality=quality,
            output_dir=img_dir,
            rng=rng,
        )

        ann_path = ann_dir / f"ann_{i:05d}.json"
        with open(ann_path, "w", encoding="utf-8") as f:
            json.dump(ann, f, indent=2, ensure_ascii=False)

        annotations.append(ann)

    # Master manifest
    manifest_path = base_dir / "manifest.json"
    manifest = {
        "dataset_name": "SME Receipt Image Benchmark Dataset",
        "version": "v2.0.0-synthetic-evaluation",
        "total_images": len(annotations),
        "target_scale_capacity": 5000,
        "classes": doc_classes,
        "languages": languages,
        "quality_categories": qualities,
        "class_distribution": {c: sum(1 for a in annotations if a["document_type"] == c) for c in doc_classes},
        "language_distribution": {l: sum(1 for a in annotations if a["language"] == l) for l in languages},
        "quality_distribution": {q: sum(1 for a in annotations if a["quality_category"] == q) for q in qualities},
        "is_synthetic": True,
        "provenance": "Synthesized with Pillow using Bengali/English text templates and optical degradation models.",
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Master manifest saved to {manifest_path} ({len(annotations)} images generated).")
    return manifest


if __name__ == "__main__":
    build_ocr_receipt_dataset(target_count=1000)
