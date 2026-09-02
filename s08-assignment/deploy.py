"""Package and deploy the Agent Framework source to Foundry Agent Service."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import time
import zipfile

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    CodeConfiguration,
    HostedAgentDefinition,
    ProtocolVersionRecord,
)
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from provision import update_env


SOURCE_FILES = (Path("hosted/main.py"), Path("hosted/requirements.txt"))


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing {name}; run 'python provision.py --save-env' first")
    return value


def build_code_zip(path: Path) -> str:
    """Build the exact flat source archive accepted by remote_build."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in SOURCE_FILES:
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, source.name)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    load_dotenv()
    endpoint = required_env("FOUNDRY_PROJECT_ENDPOINT")
    model = required_env("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    toolbox_endpoint = required_env("TOOLBOX_ENDPOINT")
    agent_name = os.getenv("FOUNDRY_HOSTED_AGENT_NAME", "s08-docs-agent")

    project = AIProjectClient(
        endpoint=endpoint,
        credential=AzureCliCredential(),
        allow_preview=True,
    )

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="s08-agent-") as temp_dir:
        code_zip = Path(temp_dir) / "s08-agent-code.zip"
        uploaded_sha = build_code_zip(code_zip)
        with code_zip.open("rb") as code_handle:
            created = project.agents.create_version_from_code(
                agent_name=agent_name,
                definition=HostedAgentDefinition(
                    cpu="0.5",
                    memory="1Gi",
                    code_configuration=CodeConfiguration(
                        runtime="python_3_13",
                        entry_point=["python", "main.py"],
                        dependency_resolution="remote_build",
                    ),
                    protocol_versions=[
                        ProtocolVersionRecord(protocol="responses", version="1.0.0")
                    ],
                    environment_variables={
                        "AZURE_AI_MODEL_DEPLOYMENT_NAME": model,
                        "TOOLBOX_ENDPOINT": toolbox_endpoint,
                    },
                ),
                code=code_handle,
                code_zip_sha256=uploaded_sha,
                description="ELVTR S08 managed document agent",
                metadata={"course": "ELVTR", "assignment": "S08"},
            )

        print(f"Created {agent_name} version {created.version}: {created.status}")
        deadline = time.monotonic() + 20 * 60
        while time.monotonic() < deadline:
            current = project.agents.get_version(agent_name, created.version)
            print(f"Provisioning status: {current.status}", flush=True)
            if current.status == "active":
                break
            if current.status == "failed":
                raise RuntimeError(f"Hosted-agent deployment failed: {dict(current)}")
            time.sleep(5)
        else:
            raise TimeoutError("Hosted agent did not become active within 20 minutes")

        downloaded = hashlib.sha256()
        for chunk in project.agents.download_code(
            agent_name, agent_version=created.version
        ):
            downloaded.update(chunk)
        if downloaded.hexdigest() != uploaded_sha:
            raise RuntimeError("Downloaded hosted code does not match uploaded SHA-256")

    elapsed = time.monotonic() - started
    update_env(
        Path(".env"),
        {
            "FOUNDRY_HOSTED_AGENT_NAME": agent_name,
            "FOUNDRY_HOSTED_AGENT_VERSION": created.version,
            "FOUNDRY_HOSTED_CODE_SHA256": uploaded_sha,
        },
    )
    print(f"Hosted source SHA-256 verified: {uploaded_sha}")
    print(f"Deployment elapsed seconds: {elapsed:.1f}")


if __name__ == "__main__":
    main()
