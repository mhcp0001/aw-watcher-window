import json
import sys
import importlib
main_mod = importlib.import_module('aw_watcher_virtualdesktop.main')


def test_oneshot(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['aw-watcher-virtualdesktop', '--oneshot'])
    monkeypatch.setenv('DISPLAY', ':0')
    monkeypatch.setattr(main_mod, 'get_current_window', lambda strategy=None: {'app': 'a', 'title': 't'})
    monkeypatch.setattr(main_mod, 'get_virtual_desktop', lambda: 5)
    main_mod.main()
    out, _ = capsys.readouterr()
    data = json.loads(out.strip())
    assert data['app'] == 'a'
    assert data['virtual_desktop'] == 5
