"""Checks for completed packaging and declarations, without executing algorithms."""
import json
import subprocess
import sys
import pytest
from cloud_scheduler.cli import main

def test_cli_help():
    """Verify cli help.

    Args:
        None.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    result=subprocess.run([sys.executable,'-m','cloud_scheduler','--help'],capture_output=True,text=True)
    assert result.returncode==0
    assert '--algorithm' in result.stdout

def test_cli_unavailable_feature(capsys):
    """Verify cli unavailable feature.

    Args:
        capsys: pytest capture fixture used to inspect the command-line error output.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(SystemExit) as e: main([])
    assert e.value.code==2
    assert 'not implemented' in capsys.readouterr().err

def test_scenario_shapes(repo_root):
    """Verify scenario shapes.

    Args:
        repo_root: Absolute repository root, derived from the test location rather than
            the working directory.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    for path in (repo_root/'data/scenarios').glob('*.json'):
        value=json.loads(path.read_text(encoding='utf-8'))
        assert len(value['servers'])==3
        assert 5<=len(value['jobs'])<=8
        assert value['expected']['greedy_count']<=value['expected']['csp_max_count']
