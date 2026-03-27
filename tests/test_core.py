import pytest
import os
import tempfile
from langgraph.graph import END

from indyforge.agents.config_worker import find_config_files
from indyforge.agents.mapreduce_graph import should_retry, RepoState, verifier
from unittest.mock import patch

# --- 1. Test find_config_files() ---
def test_find_config_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some fake config files
        spring_file = os.path.join(tmpdir, "application.yml")
        with open(spring_file, "w") as f:
            f.write("server: port: 8080")
            
        node_env = os.path.join(tmpdir, ".env.local")
        with open(node_env, "w") as f:
            f.write("DB_PASS=secret123")
            
        # Add an ignored file
        ignored_dir = os.path.join(tmpdir, "node_modules")
        os.makedirs(ignored_dir)
        ignored_file = os.path.join(ignored_dir, ".env")
        with open(ignored_file, "w") as f:
            f.write("IGNORED=true")
            
        configs = find_config_files(tmpdir)
        
        found_paths = list(configs.keys())
        assert len(found_paths) == 2, f"Expected 2 configs, found {len(found_paths)}"
        
        ecosystems = [c["ecosystem"] for c in configs.values()]
        assert "spring" in ecosystems
        assert "node" in ecosystems

# --- 2. Test JSON parsing in verifier ---
@patch("indyforge.agents.mapreduce_graph.verifier_llm")
def test_verifier_json_parsing_valid(mock_llm):
    # Setup mock to return valid JSON wrapped in markdown or just plain JSON
    mock_llm.invoke.return_value = '''
    Here is my critique:
    ```json
    {
        "valid": true,
        "hallucinations": [],
        "missing": [],
        "errors": []
    }
    ```
    '''
    # We construct a partial RepoState (just enough to satisfy the verifier's use of state keys)
    state = {
        "repo_path": "dummy",
        "overview_md": "test markdown",
        "source_evidence": ["test evidence"],
        "check_valid": False
    }
    new_state = verifier(state) # type: ignore
    assert new_state["check_valid"] is True

@patch("indyforge.agents.mapreduce_graph.verifier_llm")
def test_verifier_json_parsing_invalid(mock_llm):
    # Setup mock to return invalid or false JSON
    mock_llm.invoke.return_value = '''
    {
        "valid": false,
        "hallucinations": ["invented /api/v2 endpoint"],
        "missing": [],
        "errors": []
    }
    '''
    state = {
        "repo_path": "dummy",
        "overview_md": "test",
        "source_evidence": ["test evidence"],
        "check_valid": False
    }
    new_state = verifier(state) # type: ignore
    assert new_state["check_valid"] is False

@patch("indyforge.agents.mapreduce_graph.verifier_llm")
def test_verifier_json_parsing_malformed(mock_llm):
    # Setup mock with malformed JSON causing decode error
    mock_llm.invoke.return_value = '{"valid": true, broken json'
    state = {
        "repo_path": "dummy",
        "overview_md": "test",
        "source_evidence": ["test evidence"],
        "check_valid": False
    }
    new_state = verifier(state) # type: ignore
    # The regex won't match or the load will fail, defaulting to False
    assert new_state["check_valid"] is False

# --- 3. Test should_retry() ---
def test_should_retry_when_valid():
    state = {"check_valid": True, "iteration": 1}
    assert should_retry(state) == END # type: ignore

def test_should_retry_max_iterations():
    state = {"check_valid": False, "iteration": 3}
    assert should_retry(state) == END # type: ignore

def test_should_retry_continue():
    state = {"check_valid": False, "iteration": 2}
    assert should_retry(state) == "aggregator" # type: ignore
