"""Checks for completed packaging and declarations, without executing algorithms."""
import json
import subprocess
import sys
import pytest
from cloud_scheduler.cli import main

def test_cli_help():
    result=subprocess.run([sys.executable,'-m','cloud_scheduler','--help'],capture_output=True,text=True)
    assert result.returncode==0
    assert '--algorithm' in result.stdout

def test_cli_unavailable_feature(capsys):
    with pytest.raises(SystemExit) as e: main([])
    assert e.value.code==2
    assert 'not implemented' in capsys.readouterr().err

def test_scenario_shapes(repo_root):
    for path in (repo_root/'data/scenarios').glob('*.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        assert len(value['servers'])==3
        assert 5<=len(value['jobs'])<=8
        assert value['expected']['greedy_count']<=value['expected']['csp_max_count']
