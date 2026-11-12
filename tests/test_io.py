import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

import json
from pathlib import Path
from cloud_scheduler.io import *

def test_json_round_trip_unicode_and_spaces(tmp_path):
    folder=tmp_path/'folder with spaces'; folder.mkdir()
    path=folder/'输入.json'; payload={'name':'café','jobs':[]}
    write_json(path,payload)
    assert read_json(str(path))==payload
    assert b'\r\n' not in path.read_bytes()

def test_windows_bom(tmp_path):
    path=tmp_path/'bom.json'; path.write_text('{"jobs": []}',encoding='utf-8-sig')
    assert read_json(path)=={'jobs':[]}

def test_invalid_json(tmp_path):
    path=tmp_path/'bad.json'; path.write_text('{',encoding='utf-8')
    with pytest.raises(json.JSONDecodeError): read_json(path)

def test_nonfinite_output_rejected(tmp_path):
    with pytest.raises(ValueError): write_json(tmp_path/'bad.json',{'n':float('nan')})

@pending
def test_semantic_loaders(repo_root):
    assert load_config(repo_root/'config/default.json').slot_minutes==15
    assert len(load_servers(repo_root/'data/servers.json'))==3
    assert len(load_jobs(repo_root/'data/jobs.json'))==6

@pending
def test_malformed_job_preserved(tmp_path):
    p=tmp_path/'jobs.json'; write_json(p,[{},42])
    assert load_jobs(p)==[{},42]

@pending
def test_job_file_requires_array(tmp_path):
    path=tmp_path/'jobs.json'; write_json(path,{'jobs':[]})
    with pytest.raises(ValueError): load_jobs(path)
