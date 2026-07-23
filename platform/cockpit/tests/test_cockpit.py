import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static' / 'styles.css').read_text(encoding='utf-8')

REQUIRED_CSS_VARS = ['--gold', '--navy', '--bg', '--text', '--accent']
REQUIRED_SECTIONS = ['Investment Focus', 'Value Creation Levers']
REQUIRED_IDS = ['sidebar-brand', 'logo-mark']


def test_html_loads():
    assert '<title>BlackGold Platform Cockpit</title>' in HTML


def test_css_theme_tokens():
    for var in REQUIRED_CSS_VARS:
        assert var in CSS


def test_required_sections_present():
    for text in REQUIRED_SECTIONS:
        assert text in HTML


def test_sidebar_branding_classes_present():
    class_snippet = ''.join([line for line in HTML.splitlines() if 'class=' in line])
    for ref in REQUIRED_IDS:
        assert ref in class_snippet


def test_metric_cards_have_labels_and_values():
    values = re.findall(r'class="metric-value">([^<]+)<', HTML)
    labels = re.findall(r'class="metric-label">([^<]+)<', HTML)
    assert len(values) == len(labels)
    assert len(values) >= 3
