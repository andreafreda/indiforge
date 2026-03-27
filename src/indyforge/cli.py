
import click
import os
import shutil
from indyforge.agents.mapreduce_graph import run, CACHE_DIR_NAME
from indyforge.lang import t

def _save_repo_docs(repo_result: dict, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    
    docs_path = os.path.join(out_dir, "overview.md")
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(repo_result.get("docs", ""))
    click.echo(t("cli_docs", path=docs_path))
    
    sections = {
        "dependencies.md": "deps",
        "api.md":          "api",
        "events.md":       "events",
        "security.md":     "security",
        "sequences.md":    "sequences",
        "config.md":       "config",
        "tree.md":         "tree",
    }
    
    for filename, key in sections.items():
        content = repo_result.get(key)
        if content:
            file_path = os.path.join(out_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(t("cli_file", path=file_path))


def _cleanup_caches(repos):
    """Remove all .indyforge_cache dirs after a successful scan."""
    for r in repos:
        cache_dir = os.path.join(r, CACHE_DIR_NAME)
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir, ignore_errors=True)


@click.group()
def cli():
    pass

@cli.command()
@click.argument("repos", nargs=-1, required=True)
@click.option("--out", default="./docs", help="Output directory")
@click.option("--no-cache", is_flag=True, help="Disable and delete cache")
def scan(repos, out, no_cache):
    """Scan one or more microservices and generate full documentation."""
    click.echo(t("cli_title"))
    
    # Build list of cache dirs (one per repo, inside each repo)
    cache_dirs = [os.path.join(r, CACHE_DIR_NAME) for r in repos]
    existing_caches = [d for d in cache_dirs if os.path.exists(d) and os.listdir(d)]

    if existing_caches:
        if no_cache:
            for d in existing_caches:
                shutil.rmtree(d)
            click.echo(t("cache_flag"))
        else:
            click.echo()
            ans = input(t("cache_found") + " [Y/n]: ").strip().lower()
            if not ans or ans == 'y':
                click.echo(t("cache_used"))
            else:
                for d in existing_caches:
                    shutil.rmtree(d)
                click.echo(t("cache_deleted"))
    
    click.echo(t("cli_scan", repos=list(repos)))
    click.echo("")

    # Run the scan — if it crashes, checkpoints stay for next run
    try:
        result = run(list(repos))
    except Exception as e:
        click.echo(t("scan_crash", error=str(e)))
        raise

    # ── Save results ──────────────────────────────────────────
    os.makedirs(out, exist_ok=True)

    if "system_overview" in result:
        sys_path = os.path.join(out, "system-overview.md")
        with open(sys_path, "w", encoding="utf-8") as f:
            f.write(result["system_overview"])
        click.echo(t("cli_sysdocs", path=sys_path))
        
        for repo_docs in result.get("repo_docs", []):
            repo_name = os.path.basename(os.path.abspath(repo_docs["repo"]))
            repo_out = os.path.join(out, repo_name)
            _save_repo_docs(repo_docs, repo_out)
    else:
        _save_repo_docs(result, out)

    # ── Cleanup checkpoints after successful scan ─────────────
    _cleanup_caches(repos)
    click.echo(t("cache_cleanup"))

def main():
    cli()

if __name__ == "__main__":
    main()
