from __future__ import annotations

import json
import shutil
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from config import (
    ASSETS_DIR,
    LEGACY_PROFILE_PATH,
    OUTPUT_DIR,
    PROFILES_DIR,
    STATIC_DIR,
    TEMPLATE_PATH,
    VALID_PROFILE_ROUTES,
)


class ResumeGenerator:
    """Generate ATS-friendly resumes as HTML and PDF from JSON profiles."""

    def __init__(self) -> None:
        self.profile: dict[str, Any] = {}
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_PATH), autoescape=True)

    def load_profile(self, profile_path: Path) -> None:
        self.profile = self._read_json(profile_path)

    def generate(self) -> None:
        profile_paths = self.discover_profiles()
        profiles = self._load_profiles(profile_paths)
        self._prepare_output_dirs(OUTPUT_DIR)
        self._copy_static_assets(OUTPUT_DIR)
        self._copy_profile_image_if_present(OUTPUT_DIR)
        self.generate_gateway(profiles)

        for profile_path, profile in profiles:
            self.profile = profile
            output_dir = self._profile_output_dir(profile_path)
            self._prepare_output_dirs(output_dir)
            self._copy_static_assets(output_dir)
            self._copy_profile_image_if_present(output_dir)
            self._apply_route_theme_assets(output_dir, self._profile_route_name(profile_path))

            rendered_html = self.render_html(profile_path)
            output_name = self._output_name()
            html_path = output_dir / "index.html"
            pdf_path = output_dir / f"{output_name}_Resume.pdf"

            html_path.write_text(rendered_html, encoding="utf-8")
            self.render_pdf(rendered_html, pdf_path)

            print(f"Resume HTML written to: {html_path}")
            print(f"Resume PDF written to: {pdf_path}")

        self.generate_career_nexus_pdf(profiles)

    def discover_profiles(self) -> list[Path]:
        if PROFILES_DIR.exists():
            profile_paths = sorted(path for path in PROFILES_DIR.glob("*.json") if path.is_file())
            self._validate_profile_routes(profile_paths)
            if profile_paths:
                return profile_paths
        if LEGACY_PROFILE_PATH.exists():
            return [LEGACY_PROFILE_PATH]
        raise FileNotFoundError(f"No resume profiles found in {PROFILES_DIR}")

    def generate_gateway(self, profiles: list[tuple[Path, dict[str, Any]]]) -> None:
        template = self.env.get_template("gateway.html")
        html_path = OUTPUT_DIR / "index.html"
        html_path.write_text(
            template.render(worlds=self._career_worlds(), contacts=self._gateway_contacts(profiles)),
            encoding="utf-8",
        )
        print(f"Career gateway written to: {html_path}")

    def generate_career_nexus_pdf(self, profiles: list[tuple[Path, dict[str, Any]]]) -> None:
        template = self.env.get_template("career_nexus_pdf.html")
        pdf_profiles = []
        profile_map = {self._profile_route_name(path): profile for path, profile in profiles}
        for world in self._career_worlds():
            profile = profile_map.get(world["route"])
            if profile:
                pdf_profiles.append({**world, "profile": profile})

        html = template.render(worlds=self._career_worlds(), pdf_profiles=pdf_profiles)
        html_path = OUTPUT_DIR / "Career_Nexus.html"
        pdf_path = OUTPUT_DIR / "Career_Nexus.pdf"
        html_path.write_text(html, encoding="utf-8")
        self.render_pdf(html, pdf_path, html_path=html_path, outline=True)
        print(f"Career Nexus PDF written to: {pdf_path}")

    def render_html(self, profile_path: Path) -> str:
        route_name = self._profile_route_name(profile_path)
        template = self.env.get_template("modern.html")
        return template.render(
            profile=self.profile,
            route_name=route_name,
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

    def render_pdf(
        self,
        html: str,
        output_path: Path,
        html_path: Path | None = None,
        outline: bool = False,
    ) -> None:
        self._ensure_playwright_runtime()
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            self._render_pdf_fallback(output_path)
            return
        # Prefer the authoritative index file in the profile output directory.
        html_file = html_path or output_path.parent / "index.html"
        if not html_file.exists():
            html_file = output_path.with_suffix(".html")
            # If we have the rendered HTML content in memory, try writing it so Playwright can load it.
            try:
                html_file.write_text(html, encoding="utf-8")
            except Exception:
                pass

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.emulate_media(media="print")
                page.goto(html_file.resolve().as_uri(), wait_until="networkidle")
                page.pdf(
                    path=str(output_path),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False,
                    outline=outline,
                    tagged=True,
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

    def _prepare_output_dirs(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "static").mkdir(parents=True, exist_ok=True)
        (output_dir / "assets").mkdir(parents=True, exist_ok=True)

    def _copy_static_assets(self, output_dir: Path) -> None:
        for path in STATIC_DIR.iterdir():
            if path.is_file():
                shutil.copy2(path, output_dir / "static" / path.name)

    def _copy_profile_image_if_present(self, output_dir: Path) -> None:
        if self._has_profile_image():
            shutil.copy2(ASSETS_DIR / "profile.jpg", output_dir / "assets" / "profile.jpg")

    def _apply_route_theme_assets(self, output_dir: Path, route_name: str) -> None:
        theme = {
            "data-entry": {
                "#2f6fed": "#12a87b",
                "#1f4fd3": "#0b7d62",
                "#5d98ff": "#39d9a3",
                "#e7f0ff": "#e5fbf2",
                "#1448a8": "#087257",
            },
            "production": {
                "#2f6fed": "#d58a18",
                "#1f4fd3": "#9a5a0f",
                "#5d98ff": "#ffbf55",
                "#e7f0ff": "#fff2d8",
                "#1448a8": "#8a4f0c",
            },
        }.get(route_name)
        if not theme:
            return

        style_path = output_dir / "static" / "style.css"
        if not style_path.exists():
            return
        css = style_path.read_text(encoding="utf-8")
        for source, replacement in theme.items():
            css = css.replace(source, replacement)
        style_path.write_text(css, encoding="utf-8")

    def _has_profile_image(self) -> bool:
        return (ASSETS_DIR / "profile.jpg").exists()

    def _output_name(self) -> str:
        first_name = self.profile.get("name", "Ahmed").split()[0]
        return re.sub(r"[^A-Za-z0-9]+", "", first_name) or "Resume"

    def _load_profiles(self, profile_paths: list[Path]) -> list[tuple[Path, dict[str, Any]]]:
        return [(path, self._read_json(path)) for path in profile_paths]

    @staticmethod
    def _profile_output_dir(profile_path: Path) -> Path:
        route_name = ResumeGenerator._profile_route_name(profile_path)
        return OUTPUT_DIR / route_name

    @staticmethod
    def _profile_route_name(profile_path: Path) -> str:
        route_name = re.sub(r"[^A-Za-z0-9-]+", "-", profile_path.stem).strip("-").lower()
        if not route_name:
            route_name = "resume"
        return route_name

    @staticmethod
    def _validate_profile_routes(profile_paths: list[Path]) -> None:
        invalid_routes = sorted(
            ResumeGenerator._profile_route_name(path)
            for path in profile_paths
            if ResumeGenerator._profile_route_name(path) not in VALID_PROFILE_ROUTES
        )
        if invalid_routes:
            valid_routes = ", ".join(VALID_PROFILE_ROUTES)
            raise ValueError(
                f"Unsupported resume profile route(s): {', '.join(invalid_routes)}. "
                f"Valid routes: {valid_routes}"
            )

    @staticmethod
    def _career_worlds() -> list[dict[str, str]]:
        return [
            {
                "index": "01",
                "route": "software",
                "theme": "software",
                "title": "Software Engineering",
                "href": "software/",
                "status": "Systems online",
                "description": "Build systems, products, automation, and intelligent workflows.",
            },
            {
                "index": "02",
                "route": "data-entry",
                "theme": "data",
                "title": "Data Entry & Data Processing",
                "href": "data-entry/",
                "status": "Records aligned",
                "description": "Transform scattered records into clean, reliable structure.",
            },
            {
                "index": "03",
                "route": "production",
                "theme": "production",
                "title": "Production",
                "href": "production/",
                "status": "Flow stabilized",
                "description": "Support operational flow with consistency, quality, and focus.",
            },
        ]

    @staticmethod
    def _world_label(route_name: str) -> str:
        labels = {
            "software": "Software Engineering",
            "data-entry": "Data Entry & Data Processing",
            "production": "Production Entry Level",
        }
        return labels.get(route_name, route_name.replace("-", " ").title())

    @staticmethod
    def _gateway_contacts(profiles: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, str]]:
        if not profiles:
            return []
        labels = {
            "email": "Email",
            "whatsapp": "WhatsApp",
            "linkedin": "LinkedIn",
            "github": "GitHub",
            "portfolio": "Portfolio",
        }
        contacts = profiles[0][1].get("contacts", [])
        return [
            {"label": labels.get(item.get("type", ""), item.get("label", "")), "value": item.get("value", "#")}
            for item in contacts
        ]

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
