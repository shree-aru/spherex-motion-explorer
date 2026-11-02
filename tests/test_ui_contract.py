"""HTML/JS contract checks; no browser or network needed."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
JS = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8')

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.buttons = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        if tag == 'button': self.buttons.append(d)

def test_no_duplicate_ids_and_required_handlers():
    dom = IdParser()
    dom.feed(HTML)
    assert len(dom.ids) == len(set(dom.ids)), 'Duplicate DOM IDs will break JS queries'
    for element_id in ('searchButton', 'helpBtn', 'helpDialog', 'timelineTrack',
                       'wavelengthPlot', 'imagePane', 'observationList',
                       'exportEvidence', 'frameStage', 'atlasStage', 'playBtn'):
        assert element_id in dom.ids

def test_all_literal_id_queries_resolve():
    import re
    dom = IdParser()
    dom.feed(HTML)
    required = set(re.findall(r"\$\('([A-Za-z][A-Za-z0-9-]*)'\)", JS))
    assert not required.difference(dom.ids), f'Missing HTML ids: {required.difference(dom.ids)}'

def test_no_fake_science_content_and_ui_actions():
    assert 'Timeline will display archive timestamps' in HTML
    assert 'NOT SPHEREx' in HTML
    assert 'Photometric status' in HTML
    assert 'Not certified' in HTML
    assert 'drawTimeline()' in JS
    assert 'updateSciencePanels()' in JS
    assert 'showModal()' in JS
