from __future__ import annotations

import json
import shutil
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from config import BASE_DIR, OUTPUT_DIR, PROFILE_PATH, TEMPLATE_PATH, STATIC_DIR, ASSETS_DIR


class ResumeGenerator:
    """Generate an ATS-friendly resume as HTML and PDF from a JSON profile."""

    def __init__(self) -> None:
        self.profile: dict[str, Any] = {}
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), autoescape=True)

    def load_profile(self) -> None:
        self.profile = self._read_json(PROFILE_PATH)

    def generate(self) -> None:
        self.load_profile()
        self._prepare_output_dirs()
        self._copy_static_assets()
        self._copy_profile_image_if_present()

        rendered_html = self.render_html()
        output_name = self._output_name()
        html_path = OUTPUT_DIR / f"{output_name}_Resume.html"
        pdf_path = OUTPUT_DIR / f"{output_name}_Resume.pdf"

        html_path.write_text(rendered_html, encoding="utf-8")
        self.render_pdf(rendered_html, pdf_path)

        print(f"Resume HTML written to: {html_path}")
        print(f"Resume PDF written to: {pdf_path}")

    def render_html(self) -> str:
        template = self.env.get_template("modern.html")
        return template.render(
            profile=self.profile,
            has_profile_image=self._has_profile_image(),
            profile_image_path="assets/profile.jpg" if self._has_profile_image() else None,
            contact_items=self.profile.get("contacts", []),
            skills=self.profile.get("skills", []),
            languages=self.profile.get("languages", []),
            education_items=self.profile.get("education", []),
            certificate_items=self.profile.get("", []),
            experience_items=self.profile.get("experience", []),
            project_items=self.profile.get("projects", []),
            achievement_items=self.profile.get("achievements", []),
            technical_expertise_items=self.profile.get("technical_expertise", []),
        )

    def render_pdf(self, html: str, output_path: Path) -> None:
        self._ensure_playwright_runtime()
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            self._render_pdf_fallback(output_path)
            return

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.emulate_media(media="print")
                page.goto(output_path.with_suffix(".html").resolve().as_uri(), wait_until="networkidle")
                page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False,
                )
                browser.close()
        except Exception:
            self._render_pdf_fallback(output_path)

    def _ensure_playwright_runtime(self) -> None:
        try:
            import playwright  # noqa: F401
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as playwright:
                playwright.chromium.launch(headless=True).close()
        except Exception:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

    def _render_pdf_fallback(self, output_path: Path) -> None:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        width, height = A4
        c = canvas.Canvas(str(output_path), pagesize=A4)
        c.setTitle(f"{self.profile.get('name', 'Resume')} Resume")

        y = height - 2.2 * cm
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#1f3b6e"))
        c.drawString(2.2 * cm, y, self.profile.get("name", "Resume"))

        y -= 0.7 * cm
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#4b5a6e"))
        c.drawString(2.2 * cm, y, self.profile.get("job_title", "Professional"))

        y -= 0.8 * cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2f6fed"))
        c.drawString(2.2 * cm, y, "Contact")
        y -= 0.5 * cm
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#273547"))
        for item in self.profile.get("contacts", []):
            text = f"{item.get('type', '').title()}: {item.get('label', '')}"
            c.drawString(2.2 * cm, y, text)
            y -= 0.45 * cm

        y -= 0.3 * cm
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2f6fed"))
        c.drawString(2.2 * cm, y, "Summary")
        y -= 0.5 * cm
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#273547"))
        wrapped = self._wrap_text(self.profile.get("summary", ""), 90)
        for line in wrapped:
            c.drawString(2.2 * cm, y, line)
            y -= 0.45 * cm

        c.save()

    def _prepare_output_dirs(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "static").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "assets").mkdir(parents=True, exist_ok=True)

    def _copy_static_assets(self) -> None:
        for path in STATIC_DIR.iterdir():
            if path.is_file():
                shutil.copy2(path, OUTPUT_DIR / "static" / path.name)

    def _copy_profile_image_if_present(self) -> None:
        if self._has_profile_image():
            shutil.copy2(ASSETS_DIR / "profile.jpg", OUTPUT_DIR / "assets" / "profile.jpg")

    def _has_profile_image(self) -> bool:
        return (ASSETS_DIR / "profile.jpg").exists()

    def _output_name(self) -> str:
        first_name = self.profile.get("name", "Ahmed").split()[0]
        return re.sub(r"[^A-Za-z0-9]+", "", first_name) or "Resume"

    @staticmethod
    def _wrap_text(text: str, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


if __name__ == "__main__":
    ResumeGenerator().generate()
