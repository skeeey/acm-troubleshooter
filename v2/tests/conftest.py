import pytest
import pytest_asyncio
from git import Repo as GitRepo

from v2.server.services.db import DatabaseService

DB_URL = "sqlite+aiosqlite://"


@pytest_asyncio.fixture
async def db_svc():
    svc = DatabaseService(db_url=DB_URL)
    await svc.init_db()
    return svc


@pytest.fixture
def origin_repo(tmp_path):
    """Create a local git repo to act as a remote origin."""
    origin_path = tmp_path / "origin"
    origin_path.mkdir()
    repo = GitRepo.init(origin_path, initial_branch="main")

    test_file = origin_path / "doc.md"
    test_file.write_text("# Hello")
    repo.index.add(["doc.md"])
    repo.index.commit("initial commit")

    return origin_path
