import pytest

import json
from pathlib import Path
from cloud_scheduler.io import *

def test_json_round_trip_unicode_and_spaces(tmp_path):
    """Verify json round trip unicode and spaces.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    folder=tmp_path/'folder with spaces'; folder.mkdir()
    path=folder/'输入.json'; payload={'name':'café','jobs':[]}
    write_json(path,payload)
    assert read_json(str(path))==payload
    assert b'\r\n' not in path.read_bytes()

def test_windows_bom(tmp_path):
    """Verify windows bom.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'bom.json'; path.write_text('{"jobs": []}',encoding='utf-8-sig')
    assert read_json(path)=={'jobs':[]}

def test_invalid_json(tmp_path):
    """Verify invalid json.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'bad.json'; path.write_text('{',encoding='utf-8')
    with pytest.raises(json.JSONDecodeError): read_json(path)

def test_nonfinite_output_rejected(tmp_path):
    """Verify nonfinite output rejected.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError): write_json(tmp_path/'bad.json',{'n':float('nan')})

def test_semantic_loaders(repo_root):
    """Verify semantic loaders.

    Args:
        repo_root: Absolute repository root, derived from the test location rather than
            the working directory.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert load_config(repo_root/'config/default.json').slot_minutes==15
    assert len(load_servers(repo_root/'data/servers.json'))==3
    assert len(load_jobs(repo_root/'data/jobs.json'))==6

def test_malformed_job_preserved(tmp_path):
    """Verify malformed job preserved.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=tmp_path/'jobs.json'; write_json(p,[{},42])
    assert load_jobs(p)==[{},42]

def test_job_file_requires_array(tmp_path):
    """Verify job file requires array.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'jobs.json'; write_json(path,{'jobs':[]})
    with pytest.raises(TypeError): load_jobs(path)

def test_missing_input_file_propagates(tmp_path):
    """Verify missing input file propagates.

    Args:
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(FileNotFoundError): read_json(tmp_path/'missing.json')

@pytest.mark.parametrize('value',[None,[],{},[1,True,None],{'nested':{'jobs':[]}}])
def test_json_transport_preserves_root_types(value,tmp_path):
    """Verify json transport preserves root types.

    Args:
        value: Resource quantity or JSON value chosen for this parameterized type or
            boundary case.
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'data.json'; write_json(path,value)
    assert read_json(path) == value

@pytest.mark.parametrize('payload',[{'unknown':True},{'slot_minutes':0},{'objectives':['max_jobs','max_jobs']}])
def test_config_loader_rejects_invalid_objects(payload,tmp_path):
    """Verify config loader rejects invalid objects.

    Args:
        payload: JSON-compatible object or malformed root used as input to a semantic
            loader.
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'config.json'; write_json(path,payload)
    with pytest.raises(ValueError): load_config(path)

@pytest.mark.parametrize('payload',[None,{},42,'jobs'])
def test_job_loader_rejects_nonarray_roots(payload,tmp_path):
    """Verify job loader rejects nonarray roots.

    Args:
        payload: JSON-compatible object or malformed root used as input to a semantic
            loader.
        tmp_path: pytest temporary directory used for isolated portable filesystem
            checks.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    path=tmp_path/'jobs.json'; write_json(path,payload)
    with pytest.raises(TypeError): load_jobs(path)

@pytest.mark.parametrize('payload', [None, [], 'config', 3, True])
def test_config_requires_object(payload, tmp_path):
    """Reject non-object configuration roots before dataclass construction.

    Args:
        payload: JSON value that is not a configuration object.
        tmp_path: Isolated directory for the input file.

    Returns:
        None. Invalid root types must raise TypeError.
    """
    path = tmp_path / 'config.json'
    write_json(path, payload)
    with pytest.raises(TypeError, match='JSON object'):
        load_config(path)

@pytest.mark.parametrize('payload', [
    {'objectives': 'max_jobs'}, {'objectives': None}, {'objectives': []},
    {'objectives': [{}]}, {'objectives': [True]}, {'objectives': ['unknown']},
    {'slot_minutes': True}, {'horizon_minutes': 0}, {'slot_minutes': 7},
    {'slot_minutes': '15'}, {'search_timeout_seconds': 0},
    {'search_timeout_seconds': True}, {'use_mrv': 1},
    {'use_mac': True, 'use_backjumping': True},
])
def test_config_loader_validates_types_and_options(payload, tmp_path):
    """Apply shared configuration validation to malformed JSON field values.

    Args:
        payload: Configuration fields containing invalid types or combinations.
        tmp_path: Isolated directory for the input file.

    Returns:
        None. Structural type errors raise TypeError; invalid values raise ValueError.
    """
    path = tmp_path / 'config.json'
    write_json(path, payload)
    error = (TypeError if 'objectives' in payload
             and not isinstance(payload['objectives'], list) else ValueError)
    with pytest.raises(error):
        load_config(path)


def test_config_defaults_and_ordered_objectives(tmp_path):
    """Preserve dataclass defaults and convert configured priority arrays to tuples.

    Args:
        tmp_path: Isolated directory for configuration files.

    Returns:
        None. Assertions verify defaults and alternate priority ordering.
    """
    from cloud_scheduler.config import SchedulerConfig
    path = tmp_path / 'config.json'
    write_json(path, {})
    assert load_config(path) == SchedulerConfig()
    write_json(path, {'objectives': ['min_active_servers', 'max_jobs'],
                      'search_timeout_seconds': None})
    config = load_config(path)
    assert config.objectives == ('min_active_servers', 'max_jobs')
    assert config.search_timeout_seconds is None


@pytest.mark.parametrize('payload,error', [
    (None, TypeError), ({}, TypeError), (42, TypeError), ('servers', TypeError),
    ([None], TypeError), ([42], TypeError), ([{}], ValueError),
    ([{'server_id':'s','cpu_capacity':1,'ram_capacity_gb':1,'unknown':0}], ValueError),
    ([{'server_id':'s','cpu_capacity':True,'ram_capacity_gb':1}], ValueError),
    ([{'server_id':'s','cpu_capacity':1,'ram_capacity_gb':-1}], ValueError),
    ([{'server_id':'s','cpu_capacity':1,'ram_capacity_gb':1}]*2, ValueError),
])
def test_server_loader_rejects_malformed_inventory(payload, error, tmp_path):
    """Reject invalid root shapes, server fields, quantities and duplicate IDs.

    Args:
        payload: JSON value representing a malformed inventory.
        error: TypeError for wrong JSON types; ValueError for invalid record contents.
        tmp_path: Isolated directory for the inventory file.

    Returns:
        None. Each malformed inventory raises the documented exception type.
    """
    path = tmp_path / 'servers.json'
    write_json(path, payload)
    with pytest.raises(error):
        load_servers(path)


def test_server_defaults_input_order_and_empty_inventory(tmp_path):
    """Preserve server order and optional defaults, including an empty cluster.

    Args:
        tmp_path: Isolated directory for the inventory file.

    Returns:
        None. Loaded servers retain file order and dataclass defaults.
    """
    path = tmp_path / 'servers.json'
    write_json(path, [{'server_id':name,'cpu_capacity':1,'ram_capacity_gb':2}
                      for name in ('z','a')])
    servers = load_servers(path)
    assert tuple(s.server_id for s in servers) == ('z','a')
    assert all(s.gpu_capacity == 0 and s.storage_capacity_gb == 0 for s in servers)
    write_json(path, [])
    assert load_servers(path) == ()


def test_job_loader_preserves_invalid_records_and_order(tmp_path):
    """Keep every raw submission for later indexed validation rather than filtering.

    Args:
        tmp_path: Isolated directory for the job file.

    Returns:
        None. Payload values and order survive semantic loading unchanged.
    """
    payload = [{}, None, 42, True, 'job', [], {'job_id':'duplicate'},
               {'job_id':'duplicate'}]
    path = tmp_path / 'jobs.json'
    write_json(path, payload)
    assert load_jobs(path) == payload
    write_json(path, [])
    assert load_jobs(path) == []


@pytest.mark.parametrize('loader', [load_config, load_servers, load_jobs])
def test_semantic_loader_file_and_json_errors(loader, tmp_path):
    """Propagate missing-file and JSON-syntax errors from every semantic loader.

    Args:
        loader: Configuration, server or job loading function.
        tmp_path: Isolated directory for missing and malformed files.

    Returns:
        None. File and syntax failures retain their original exception types.
    """
    with pytest.raises(FileNotFoundError):
        loader(tmp_path / 'missing.json')
    path = tmp_path / 'broken.json'
    path.write_text('{', encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):
        loader(path)


@pytest.mark.parametrize('filename,loader,payload', [
    ('config.json', load_config, {}),
    ('servers.json', load_servers, []),
    ('jobs.json', load_jobs, []),
])
def test_semantic_loaders_accept_bom_and_paths_with_spaces(filename, loader, payload, tmp_path):
    """Support Windows BOM input and portable Unicode paths containing spaces.

    Args:
        filename: Input file name for the selected loader.
        loader: Semantic loading function under test.
        payload: Minimal valid JSON value for that loader.
        tmp_path: Isolated directory for portable path checks.

    Returns:
        None. Valid BOM-prefixed files load through both str and Path inputs.
    """
    folder = tmp_path / 'données with spaces'
    folder.mkdir()
    path = folder / filename
    path.write_text(json.dumps(payload), encoding='utf-8-sig')
    assert loader(str(path)) == loader(path)


def test_loaded_default_inputs_validate(repo_root):
    """Connect the three loaders to per-record validation of the default batch.

    Args:
        repo_root: Absolute repository root containing default example inputs.

    Returns:
        None. All default submissions validate with resolved deadlines and no errors.
    """
    from cloud_scheduler.preprocessing import validate_jobs
    config = load_config(repo_root / 'config' / 'default.json')
    servers = load_servers(repo_root / 'data' / 'servers.json')
    jobs = load_jobs(repo_root / 'data' / 'jobs.json')
    valid, invalid = validate_jobs(jobs, config)
    assert len(servers) == 3 and len(valid) == 6
    assert not invalid
    assert all(job.deadline_minute is not None for job in valid)
